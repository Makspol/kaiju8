from dataclasses import dataclass
from math import ceil


DEFAULT_PROVIDER_MAX_LLM_CALLS = 20
SUPPORTED_AI_LIMIT_PROVIDERS = ("claude", "gemini")
NODE_AI_LIMIT_KEYS = ("budget", "max_llm_calls", "max_tokens")


class ExecutionLimitExceeded(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class RuntimeUsage:
    llm_calls: int = 0
    tokens_used: int = 0
    budget_used: float = 0.0
    by_provider: dict[str, "RuntimeUsage"] | None = None

    def as_dict(self) -> dict:
        result = {
            "llm_calls": self.llm_calls,
            "tokens_used": self.tokens_used,
            "budget_used": round(self.budget_used, 8),
        }

        if self.by_provider:
            result["by_provider"] = {
                provider: usage.as_dict()
                for provider, usage in self.by_provider.items()
            }

        return result

    def provider_usage(self, provider: str) -> "RuntimeUsage":
        if self.by_provider is None:
            self.by_provider = {}

        if provider not in self.by_provider:
            self.by_provider[provider] = RuntimeUsage()

        return self.by_provider[provider]


def estimate_tokens(text: str | None) -> int:
    if not text:
        return 0

    return max(1, ceil(len(text) / 4))


def normalize_ai_limits(value: object) -> dict[str, dict]:
    limits = {
        provider: {"max_llm_calls": DEFAULT_PROVIDER_MAX_LLM_CALLS}
        for provider in SUPPORTED_AI_LIMIT_PROVIDERS
    }

    if not isinstance(value, dict):
        return limits

    for provider, provider_limits in value.items():
        if not isinstance(provider_limits, dict):
            continue

        limits[provider] = {
            **limits.get(provider, {}),
            **provider_limits,
        }

    return limits


def normalize_node_ai_limits(value: object) -> dict:
    if not isinstance(value, dict):
        return {}

    limits = {}

    for key in NODE_AI_LIMIT_KEYS:
        item = value.get(key)

        if item is not None:
            limits[key] = item

    return limits
