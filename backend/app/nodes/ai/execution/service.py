from time import monotonic

from app.nodes.ai.execution.api_keys import resolve_api_key
from app.nodes.ai.execution.knowledge import resolve_knowledge_items
from app.nodes.ai.execution.prompt import build_agent_prompt
from app.nodes.ai.execution.providers import ProviderRegistry
from app.nodes.ai.execution.tools import run_tools
from app.runtime.limits import ExecutionLimitExceeded, estimate_tokens
from app.runtime.types import ExecutionContext


DEFAULT_AI_TOKEN_COSTS = {
    "claude": {"input_per_1m": 3.0, "output_per_1m": 15.0},
    "gemini": {"input_per_1m": 0.30, "output_per_1m": 2.50},
}


class AiExecutionService:
    def __init__(self, provider_registry: ProviderRegistry | None = None):
        self.provider_registry = provider_registry or ProviderRegistry()

    def execute_agent(
        self,
        prompt: str | None,
        model: dict,
        memory: dict,
        tools: list[dict],
        knowledge: list[dict],
        input_data: dict,
        context: ExecutionContext,
        timeout_seconds: float | None = None,
    ) -> dict:
        started_at = monotonic()
        provider_name = model.get("provider", "claude")
        provider = self.provider_registry.get(provider_name)

        if provider is None:
            return {
                "status": "failed",
                "error": f"Unsupported AI provider: {provider_name}",
                "response": None,
                "prompt": prompt,
                "tool_results": [],
                "knowledge": knowledge,
            }

        try:
            _ensure_agent_not_timed_out(started_at, timeout_seconds)
            resolved_knowledge = resolve_knowledge_items(
                knowledge=knowledge,
                owner_user_id=context.owner_user_id,
            )
            _ensure_agent_not_timed_out(started_at, timeout_seconds)
            tool_results = run_tools(
                tools,
                input_data=input_data,
                owner_user_id=context.owner_user_id,
                timeout_seconds=_remaining_timeout(started_at, timeout_seconds),
            )
            _ensure_agent_not_timed_out(started_at, timeout_seconds)
        except ExecutionLimitExceeded as error:
            return _limit_error_response(
                error=error,
                prompt=prompt or "",
                tool_results=[],
                knowledge=knowledge,
                usage=context.usage.as_dict(),
            )

        final_prompt = build_agent_prompt(
            prompt=prompt,
            input_data=input_data,
            memory=memory,
            knowledge=resolved_knowledge,
            tool_results=tool_results,
        )
        estimated_input_tokens = estimate_tokens(final_prompt)
        api_key = resolve_api_key(
            provider_name,
            model,
            owner_user_id=context.owner_user_id,
        )

        if not api_key:
            return {
                "status": "missing_api_key",
                "error": _missing_key_message(provider_name),
                "response": None,
                "prompt": final_prompt,
                "tool_results": tool_results,
                "knowledge": resolved_knowledge,
                "usage": context.usage.as_dict(),
            }

        node_limits = _node_limits(model)

        try:
            _ensure_agent_not_timed_out(started_at, timeout_seconds)
            context.reserve_llm_call(
                provider_name,
                estimated_input_tokens,
                node_limits=node_limits,
            )
            _ensure_agent_not_timed_out(started_at, timeout_seconds)
        except ExecutionLimitExceeded as error:
            return _limit_error_response(
                error=error,
                prompt=final_prompt,
                tool_results=tool_results,
                knowledge=resolved_knowledge,
                usage=context.usage.as_dict(),
            )

        try:
            provider_response = provider.generate(
                prompt=final_prompt,
                api_key=api_key,
                model=model.get("model_name"),
                timeout_seconds=_remaining_timeout(started_at, timeout_seconds),
            )
            _ensure_agent_not_timed_out(started_at, timeout_seconds)
        except Exception as error:
            try:
                _ensure_agent_not_timed_out(started_at, timeout_seconds)
            except ExecutionLimitExceeded as limit_error:
                return _limit_error_response(
                    error=limit_error,
                    prompt=final_prompt,
                    tool_results=tool_results,
                    knowledge=resolved_knowledge,
                    usage=context.usage.as_dict(),
                )

            return {
                "status": "failed",
                "error": str(error),
                "response": None,
                "prompt": final_prompt,
                "tool_results": tool_results,
                "knowledge": resolved_knowledge,
                "usage": context.usage.as_dict(),
            }

        input_tokens = provider_response.input_tokens or estimated_input_tokens
        output_tokens = provider_response.output_tokens or estimate_tokens(provider_response.text)
        budget_cost = _estimate_budget_cost(
            provider_name=provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        try:
            _ensure_agent_not_timed_out(started_at, timeout_seconds)
            context.record_llm_result(
                provider=provider_name,
                output_tokens=output_tokens,
                budget_cost=budget_cost,
                node_limits=node_limits,
                node_input_tokens=input_tokens,
            )
        except ExecutionLimitExceeded as error:
            return _limit_error_response(
                error=error,
                prompt=final_prompt,
                tool_results=tool_results,
                knowledge=resolved_knowledge,
                usage=context.usage.as_dict(),
            )

        return {
            "status": "success",
            "error": None,
            "response": provider_response.text,
            "prompt": final_prompt,
            "tool_results": tool_results,
            "knowledge": resolved_knowledge,
            "raw_response": provider_response.raw,
            "usage": context.usage.as_dict(),
            "llm_usage": {
                "provider": provider_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "budget_cost": round(budget_cost, 8),
            },
        }


def _missing_key_message(provider_name: str) -> str:
    if provider_name == "claude":
        return "Add an Anthropic credential or set ANTHROPIC_API_KEY."

    if provider_name == "gemini":
        return "Add a Gemini credential or set GEMINI_API_KEY."

    return "Missing AI provider API key."


def _limit_error_response(
    error: ExecutionLimitExceeded,
    prompt: str,
    tool_results: list[dict],
    knowledge: list[dict],
    usage: dict,
) -> dict:
    return {
        "status": error.code,
        "error": error.message,
        "response": None,
        "prompt": prompt,
        "tool_results": tool_results,
        "knowledge": knowledge,
        "usage": usage,
    }


def _estimate_budget_cost(
    provider_name: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    default_costs = DEFAULT_AI_TOKEN_COSTS.get(provider_name, {})
    input_cost = float(default_costs.get("input_per_1m") or 0)
    output_cost = float(default_costs.get("output_per_1m") or 0)

    return (input_tokens / 1_000_000 * input_cost) + (output_tokens / 1_000_000 * output_cost)


def _node_limits(model: dict) -> dict:
    return {
        key: model[key]
        for key in ("budget", "max_llm_calls", "max_tokens")
        if model.get(key) is not None
    }


def _ensure_agent_not_timed_out(
    started_at: float,
    timeout_seconds: float | None,
) -> None:
    if timeout_seconds is None:
        return

    if monotonic() - started_at >= timeout_seconds:
        raise ExecutionLimitExceeded(
            code="ai_node_timeout_exceeded",
            message="AI Agent timeout limit was exceeded.",
        )


def _remaining_timeout(
    started_at: float,
    timeout_seconds: float | None,
) -> float | None:
    if timeout_seconds is None:
        return None

    remaining = timeout_seconds - (monotonic() - started_at)

    if remaining <= 0:
        raise ExecutionLimitExceeded(
            code="ai_node_timeout_exceeded",
            message="AI Agent timeout limit was exceeded.",
        )

    return max(remaining, 0.001)
