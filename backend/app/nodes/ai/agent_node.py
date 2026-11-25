from time import monotonic

from app.nodes.ai.execution import AiExecutionService
from app.nodes.ai.module_config import (
    normalize_agent_modules,
    validate_agent_modules,
)
from app.nodes.ai.schemas import agent_config_schema
from app.nodes.ai.validation import (
    validate_knowledge_module,
    validate_memory_module,
    validate_model_module,
    validate_prompt,
    validate_tools_module,
)
from app.nodes.base import NodeExecutor
from app.nodes.helpers import get_by_path, set_by_path
from app.runtime.limits import ExecutionLimitExceeded
from app.runtime.types import ExecutionContext, NodeResult


class AiAgentNode(NodeExecutor):
    type = "ai.agent"
    category = "ai"
    label = "AI Agent"
    description = "Runs a model with memory, knowledge, and tools such as HTTP requests."
    config_schema = agent_config_schema()

    def __init__(self, execution_service: AiExecutionService | None = None):
        self.execution_service = execution_service or AiExecutionService()

    def validate_config(self, config: dict) -> list[str]:
        normalized_modules = normalize_agent_modules(config)

        return [
            *validate_prompt(config),
            *validate_agent_modules(config.get("modules")),
            *validate_model_module(normalized_modules["model"]),
            *validate_memory_module(normalized_modules["memory"]),
            *validate_tools_module(normalized_modules["tools"]),
            *validate_knowledge_module(normalized_modules["knowledge"]),
        ]

    def execute(
        self,
        config: dict,
        input_data: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        modules = normalize_agent_modules(config)
        model = _normalize_model_module(modules["model"])
        memory = _normalize_memory_module(modules["memory"])
        tools = modules["tools"]
        knowledge = modules["knowledge"]
        prompt = config.get("prompt")
        timeout_seconds = _timeout_seconds(config)
        started_at = monotonic()
        execution = self.execution_service.execute_agent(
            prompt=prompt,
            model=modules["model"],
            memory=memory,
            tools=tools,
            knowledge=knowledge,
            input_data=input_data,
            context=context,
            timeout_seconds=timeout_seconds,
        )

        if execution["status"] in {
            "timeout_exceeded",
            "ai_node_timeout_exceeded",
            "max_llm_calls_exceeded",
            "max_tokens_exceeded",
            "budget_exceeded",
            "claude_max_llm_calls_exceeded",
            "claude_max_tokens_exceeded",
            "claude_budget_exceeded",
            "gemini_max_llm_calls_exceeded",
            "gemini_max_tokens_exceeded",
            "gemini_budget_exceeded",
            "ai_node_max_llm_calls_exceeded",
            "ai_node_max_tokens_exceeded",
            "ai_node_budget_exceeded",
        }:
            raise ExecutionLimitExceeded(
                code=execution["status"],
                message=execution["error"] or "Workflow AI execution limit was exceeded.",
            )

        _ensure_node_timeout_not_exceeded(started_at, timeout_seconds)

        output = dict(input_data)
        ai_output = {
            "kind": "agent",
            "provider": model["provider"],
            "prompt": execution["prompt"],
            "model": model,
            "memory": memory,
            "tools": tools,
            "knowledge": execution["knowledge"],
            "modules": modules["modules"],
            "tool_results": execution["tool_results"],
            "response": execution["response"],
            "error": execution["error"],
            "status": execution["status"],
            "usage": execution.get("usage"),
        }
        output["ai"] = ai_output

        if "raw_response" in execution:
            ai_output["raw_response"] = execution["raw_response"]

        if "llm_usage" in execution:
            ai_output["llm_usage"] = execution["llm_usage"]

        output_path = _output_path(config)

        if output_path:
            set_by_path(
                output,
                output_path,
                execution["response"] or execution["error"] or "",
            )

        route = _resolve_route(config=config, input_data=input_data, ai_output=ai_output)

        if route:
            output["route"] = route

        return NodeResult(output=output)


def _normalize_model_module(value: dict) -> dict:
    model = {
        "provider": value.get("provider", "claude"),
        "api_key_configured": bool(
            value.get("credential_id")
            or value.get("api_key")
            or value.get("api_key_ref")
        ),
    }

    if value.get("model_name"):
        model["model_name"] = value["model_name"]

    return model


def _normalize_memory_module(value: dict) -> dict:
    memory = {
        "enabled": value.get("enabled", True),
        "history": value.get("history", []),
    }

    if value.get("files"):
        memory["files"] = value["files"]

    return memory


def _output_path(config: dict) -> str:
    return str(config.get("output_path") or config.get("outputPath") or "").strip()


def _timeout_seconds(config: dict) -> float | None:
    value = config.get("timeout_seconds", config.get("timeoutSeconds"))

    if not isinstance(value, (int, float)) or value <= 0:
        return None

    return float(value)


def _ensure_node_timeout_not_exceeded(
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


def _resolve_route(config: dict, input_data: dict, ai_output: dict) -> str | None:
    routing = config.get("routing")

    if not isinstance(routing, dict) or not routing.get("enabled", True):
        return None

    strategy = str(routing.get("strategy") or "field_match").strip().lower()

    if strategy == "field_match":
        return _route_from_field_match(routing, input_data)

    if strategy == "ai_response":
        response = ai_output.get("response") or ai_output.get("error") or ""
        return _route_from_text(str(response), routing)

    return None


def _route_from_field_match(routing: dict, input_data: dict) -> str | None:
    field = str(routing.get("field") or "").strip()

    if not field:
        return _default_route(routing)

    value = get_by_path(input_data, field)
    value_text = "" if value is None else str(value).strip().lower()

    for route in _route_entries(routing):
        matches = route.get("match", route.get("value"))

        if not isinstance(matches, list):
            matches = [matches]

        for match in matches:
            if match is not None and str(match).strip().lower() == value_text:
                return _route_name(route)

    return _default_route(routing)


def _route_from_text(text: str, routing: dict) -> str | None:
    normalized = text.strip().lower()

    for route in _route_entries(routing):
        route_name = _route_name(route)

        if route_name and route_name.lower() == normalized:
            return route_name

    return _default_route(routing)


def _route_entries(routing: dict) -> list[dict]:
    routes = routing.get("routes", [])
    return [
        route
        for route in routes
        if isinstance(route, dict)
    ]


def _route_name(route: dict) -> str | None:
    value = route.get("route") or route.get("name") or route.get("label")

    if value is None:
        return None

    return str(value).strip() or None


def _default_route(routing: dict) -> str | None:
    value = routing.get("default_route") or routing.get("defaultRoute")

    if value is None:
        return None

    return str(value).strip() or None
