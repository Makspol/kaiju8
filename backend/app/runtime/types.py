from dataclasses import dataclass, field
from time import monotonic
from typing import Any

from app.runtime.limits import (
    ExecutionLimitExceeded,
    RuntimeUsage,
    normalize_ai_limits,
    normalize_node_ai_limits,
)


JSON = dict[str, Any]


@dataclass
class NodeResult:
    output: JSON
    final: bool = False


@dataclass
class ExecutionContext:
    initial_input: JSON
    owner_user_id: str | None = None
    trigger_node_id: str | None = None
    trigger_node_type: str | None = None
    max_steps: int = 20
    timeout_seconds: float | None = None
    budget: float | None = None
    max_llm_calls: int | None = None
    max_tokens: int | None = None
    ai_limits: dict[str, JSON] = field(default_factory=dict)
    started_at: float = field(default_factory=monotonic)
    usage: RuntimeUsage = field(default_factory=RuntimeUsage)
    node_outputs: dict[str, JSON] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.ai_limits = normalize_ai_limits(self.ai_limits)

    @property
    def triggered_by_chat(self) -> bool:
        return self.trigger_node_type == "chat.trigger"

    @property
    def timed_out(self) -> bool:
        if self.timeout_seconds is None:
            return False

        return monotonic() - self.started_at >= self.timeout_seconds

    def ensure_not_timed_out(self) -> None:
        if self.timed_out:
            raise ExecutionLimitExceeded(
                code="timeout_exceeded",
                message="Workflow timeout limit was exceeded.",
            )

    def reserve_llm_call(
        self,
        provider: str,
        estimated_input_tokens: int,
        node_limits: JSON | None = None,
    ) -> None:
        self.ensure_not_timed_out()
        provider_usage = self.usage.provider_usage(provider)
        provider_limits = self.ai_limits.get(provider, {})
        node_limits = normalize_node_ai_limits(node_limits)

        if (
            self.max_llm_calls is not None
            and self.usage.llm_calls + 1 > self.max_llm_calls
        ):
            raise ExecutionLimitExceeded(
                code="max_llm_calls_exceeded",
                message="Workflow LLM call limit was exceeded.",
            )

        provider_max_calls = provider_limits.get("max_llm_calls")
        if (
            provider_max_calls is not None
            and provider_usage.llm_calls + 1 > provider_max_calls
        ):
            raise ExecutionLimitExceeded(
                code=f"{provider}_max_llm_calls_exceeded",
                message=f"{provider} LLM call limit was exceeded.",
            )

        node_max_calls = node_limits.get("max_llm_calls")
        if node_max_calls is not None and 1 > node_max_calls:
            raise ExecutionLimitExceeded(
                code="ai_node_max_llm_calls_exceeded",
                message="AI node LLM call limit was exceeded.",
            )

        if (
            self.max_tokens is not None
            and self.usage.tokens_used + estimated_input_tokens > self.max_tokens
        ):
            raise ExecutionLimitExceeded(
                code="max_tokens_exceeded",
                message="Workflow token limit was exceeded before the model call.",
            )

        provider_max_tokens = provider_limits.get("max_tokens")
        if (
            provider_max_tokens is not None
            and provider_usage.tokens_used + estimated_input_tokens > provider_max_tokens
        ):
            raise ExecutionLimitExceeded(
                code=f"{provider}_max_tokens_exceeded",
                message=f"{provider} token limit was exceeded before the model call.",
            )

        node_max_tokens = node_limits.get("max_tokens")
        if (
            node_max_tokens is not None
            and estimated_input_tokens > node_max_tokens
        ):
            raise ExecutionLimitExceeded(
                code="ai_node_max_tokens_exceeded",
                message="AI node token limit was exceeded before the model call.",
            )

        self.usage.llm_calls += 1
        self.usage.tokens_used += estimated_input_tokens
        provider_usage.llm_calls += 1
        provider_usage.tokens_used += estimated_input_tokens

    def record_llm_result(
        self,
        provider: str,
        output_tokens: int,
        budget_cost: float = 0.0,
        node_limits: JSON | None = None,
        node_input_tokens: int = 0,
    ) -> None:
        provider_usage = self.usage.provider_usage(provider)
        provider_limits = self.ai_limits.get(provider, {})
        node_limits = normalize_node_ai_limits(node_limits)

        self.usage.tokens_used += max(output_tokens, 0)
        self.usage.budget_used += max(budget_cost, 0.0)
        provider_usage.tokens_used += max(output_tokens, 0)
        provider_usage.budget_used += max(budget_cost, 0.0)
        node_tokens = max(node_input_tokens, 0) + max(output_tokens, 0)

        if self.max_tokens is not None and self.usage.tokens_used > self.max_tokens:
            raise ExecutionLimitExceeded(
                code="max_tokens_exceeded",
                message="Workflow token limit was exceeded after the model call.",
            )

        provider_max_tokens = provider_limits.get("max_tokens")
        if (
            provider_max_tokens is not None
            and provider_usage.tokens_used > provider_max_tokens
        ):
            raise ExecutionLimitExceeded(
                code=f"{provider}_max_tokens_exceeded",
                message=f"{provider} token limit was exceeded after the model call.",
            )

        node_max_tokens = node_limits.get("max_tokens")
        if node_max_tokens is not None and node_tokens > node_max_tokens:
            raise ExecutionLimitExceeded(
                code="ai_node_max_tokens_exceeded",
                message="AI node token limit was exceeded after the model call.",
            )

        if self.budget is not None and self.usage.budget_used > self.budget:
            raise ExecutionLimitExceeded(
                code="budget_exceeded",
                message="Workflow AI budget limit was exceeded.",
            )

        provider_budget = provider_limits.get("budget")
        if (
            provider_budget is not None
            and provider_usage.budget_used > provider_budget
        ):
            raise ExecutionLimitExceeded(
                code=f"{provider}_budget_exceeded",
                message=f"{provider} AI budget limit was exceeded.",
            )

        node_budget = node_limits.get("budget")
        if node_budget is not None and budget_cost > node_budget:
            raise ExecutionLimitExceeded(
                code="ai_node_budget_exceeded",
                message="AI node budget limit was exceeded.",
            )
