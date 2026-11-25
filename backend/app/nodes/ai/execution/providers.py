import json
import urllib.error
import urllib.request
from dataclasses import dataclass


DEFAULT_MODELS = {
    "claude": "claude-sonnet-4-6",
    "gemini": "gemini-2.5-flash",
}


@dataclass(frozen=True)
class AiProviderResponse:
    text: str
    raw: dict
    input_tokens: int = 0
    output_tokens: int = 0


class AiProvider:
    provider = ""

    def generate(
        self,
        prompt: str,
        api_key: str,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> AiProviderResponse:
        raise NotImplementedError


class ClaudeProvider(AiProvider):
    provider = "claude"

    def generate(
        self,
        prompt: str,
        api_key: str,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> AiProviderResponse:
        payload = {
            "model": model or DEFAULT_MODELS[self.provider],
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }
        response = _post_json(
            url="https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            payload=payload,
            timeout_seconds=timeout_seconds,
        )

        return AiProviderResponse(
            text=_extract_claude_text(response),
            raw=response,
            input_tokens=_extract_claude_input_tokens(response),
            output_tokens=_extract_claude_output_tokens(response),
        )


class GeminiProvider(AiProvider):
    provider = "gemini"

    def generate(
        self,
        prompt: str,
        api_key: str,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> AiProviderResponse:
        model_name = model or DEFAULT_MODELS[self.provider]
        response = _post_json(
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            payload={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt,
                            }
                        ]
                    }
                ]
            },
            timeout_seconds=timeout_seconds,
        )

        return AiProviderResponse(
            text=_extract_gemini_text(response),
            raw=response,
            input_tokens=_extract_gemini_input_tokens(response),
            output_tokens=_extract_gemini_output_tokens(response),
        )


class ProviderRegistry:
    def __init__(self):
        self.providers = {
            "claude": ClaudeProvider(),
            "gemini": GeminiProvider(),
        }

    def get(self, provider: str) -> AiProvider | None:
        return self.providers.get(provider)


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict,
    timeout_seconds: float | None = None,
) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=_request_timeout(timeout_seconds, default=30),
        ) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = {"error": raw}

        parsed.setdefault("status", error.code)
        raise RuntimeError(parsed) from error


def _request_timeout(value: float | None, default: int) -> float:
    if value is None:
        return float(default)

    return max(float(value), 0.001)


def _extract_claude_text(response: dict) -> str:
    parts = response.get("content", [])
    texts = [
        part.get("text", "")
        for part in parts
        if isinstance(part, dict) and part.get("type") == "text"
    ]

    return "\n".join(text for text in texts if text)


def _extract_claude_input_tokens(response: dict) -> int:
    usage = response.get("usage", {})
    return int(usage.get("input_tokens") or 0)


def _extract_claude_output_tokens(response: dict) -> int:
    usage = response.get("usage", {})
    return int(usage.get("output_tokens") or 0)


def _extract_gemini_text(response: dict) -> str:
    candidates = response.get("candidates", [])

    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [
        part.get("text", "")
        for part in parts
        if isinstance(part, dict)
    ]

    return "\n".join(text for text in texts if text)


def _extract_gemini_input_tokens(response: dict) -> int:
    usage = response.get("usageMetadata", {})
    return int(usage.get("promptTokenCount") or 0)


def _extract_gemini_output_tokens(response: dict) -> int:
    usage = response.get("usageMetadata", {})
    return int(usage.get("candidatesTokenCount") or 0)
