import json
import os
import urllib.parse
import urllib.error
import urllib.request
from typing import Any

from app.modules.credentials.service import get_credential_secret
from app.nodes.helpers import resolve_template


def run_tools(
    tools: list[dict],
    input_data: dict | None = None,
    owner_user_id: str | None = None,
    timeout_seconds: float | None = None,
) -> list[dict]:
    input_data = input_data or {}

    return [
        _run_tool(tool, input_data, owner_user_id, timeout_seconds)
        for tool in tools
    ]


def _run_tool(
    tool: dict,
    input_data: dict,
    owner_user_id: str | None,
    timeout_seconds: float | None,
) -> dict:
    tool_type = tool.get("type")

    if tool_type == "http_request":
        return _run_http_request_tool(
            tool.get("config", {}),
            input_data,
            owner_user_id,
            timeout_seconds,
        )

    if tool_type == "web_search":
        return _run_web_search_tool(
            tool.get("config", {}),
            input_data,
            owner_user_id,
            timeout_seconds,
        )

    return {
        "type": tool_type,
        "status": "skipped",
        "error": "unsupported_tool",
    }


def _run_http_request_tool(
    config: dict,
    input_data: dict,
    owner_user_id: str | None,
    timeout_seconds: float | None,
) -> dict:
    method = str(config.get("method", "GET")).upper()
    url = str(resolve_template(config.get("url", ""), input_data)).strip()
    live = bool(config.get("live", False))
    headers = _resolve_headers(config.get("headers", {}), input_data)
    body = _resolve_body(config.get("body"), input_data)
    headers = _inject_api_key_header(
        config=config,
        headers=headers,
        owner_user_id=owner_user_id,
        provider=None,
    )

    if not live:
        return {
            "type": "http_request",
            "status": "dry_run",
            "request": {
                "method": method,
                "url": url,
                "headers": _redact_headers(headers),
                "body": body,
            },
        }

    if not url.startswith(("http://", "https://")):
        return {
            "type": "http_request",
            "status": "failed",
            "error": "url must start with http:// or https://.",
        }

    try:
        response = _call_json_endpoint(url, method, headers, body, timeout_seconds)
        return {
            "type": "http_request",
            "status": "success",
            "request": {
                "method": method,
                "url": url,
                "headers": _redact_headers(headers),
                "body": body,
            },
            "response": response,
        }
    except (urllib.error.URLError, TimeoutError) as error:
        return {
            "type": "http_request",
            "status": "failed",
            "error": str(error),
        }


def _run_web_search_tool(
    config: dict,
    input_data: dict,
    owner_user_id: str | None,
    timeout_seconds: float | None,
) -> dict:
    provider = str(config.get("provider") or "brave").lower()
    query = str(resolve_template(config.get("query", ""), input_data)).strip()
    max_results = _positive_int(config.get("max_results"), default=5)
    live = bool(config.get("live", False))
    request = {
        "provider": provider,
        "query": query,
        "max_results": max_results,
    }

    if not query:
        return {
            "type": "web_search",
            "status": "failed",
            "error": "query is required.",
            "request": request,
        }

    if not live:
        return {
            "type": "web_search",
            "status": "dry_run",
            "request": request,
            "results": [],
        }

    try:
        response = _call_search_provider(
            provider=provider,
            query=query,
            max_results=max_results,
            config=config,
            owner_user_id=owner_user_id,
            timeout_seconds=timeout_seconds,
        )
    except ValueError as error:
        return {
            "type": "web_search",
            "status": "failed",
            "error": str(error),
            "request": request,
        }
    except (urllib.error.URLError, TimeoutError) as error:
        return {
            "type": "web_search",
            "status": "failed",
            "error": str(error),
            "request": request,
        }

    return {
        "type": "web_search",
        "status": "success",
        "request": request,
        "results": _extract_search_results(provider, response, max_results),
        "response": response,
    }


def _call_search_provider(
    provider: str,
    query: str,
    max_results: int,
    config: dict,
    owner_user_id: str | None,
    timeout_seconds: float | None,
) -> Any:
    if provider == "brave":
        api_key = _resolve_api_key(
            config,
            default_ref="BRAVE_SEARCH_API_KEY",
            owner_user_id=owner_user_id,
            provider="brave",
        )

        if not api_key:
            raise ValueError("Add a Brave Search credential or set BRAVE_SEARCH_API_KEY.")

        url = _append_query(
            "https://api.search.brave.com/res/v1/web/search",
            {"q": query, "count": max_results},
        )
        return _call_json_endpoint(
            url=url,
            method="GET",
            headers={
                "X-Subscription-Token": api_key,
                "Accept": "application/json",
            },
            body=None,
            timeout_seconds=timeout_seconds,
        )["body"]

    if provider == "tavily":
        api_key = _resolve_api_key(
            config,
            default_ref="TAVILY_API_KEY",
            owner_user_id=owner_user_id,
            provider="tavily",
        )

        if not api_key:
            raise ValueError("Add a Tavily credential or set TAVILY_API_KEY.")

        return _call_json_endpoint(
            url="https://api.tavily.com/search",
            method="POST",
            headers={"Content-Type": "application/json"},
            body={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout_seconds=timeout_seconds,
        )["body"]

    if provider == "custom":
        endpoint = str(resolve_template(config.get("endpoint", ""), {"query": query})).strip()

        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("endpoint must start with http:// or https://.")

        headers = _resolve_headers(config.get("headers", {}), {"query": query})
        headers = _inject_api_key_header(
            config=config,
            headers=headers,
            owner_user_id=owner_user_id,
            provider="custom",
        )

        url = _append_query(
            endpoint,
            {
                str(config.get("query_param") or "q"): query,
                str(config.get("max_results_param") or "count"): max_results,
            },
        )
        return _call_json_endpoint(
            url=url,
            method="GET",
            headers=headers,
            body=None,
            timeout_seconds=timeout_seconds,
        )["body"]

    raise ValueError("provider must be brave, tavily, or custom.")


def _resolve_headers(value: Any, input_data: dict) -> dict[str, str]:
    headers = {}

    if not isinstance(value, dict):
        return headers

    for key, raw_value in value.items():
        resolved = resolve_template(raw_value, input_data)
        headers[str(key)] = "" if resolved is None else str(resolved)

    return headers


def _resolve_body(value: Any, input_data: dict) -> Any:
    resolved = resolve_template(value, input_data)

    if isinstance(resolved, str):
        try:
            return json.loads(resolved)
        except ValueError:
            return resolved

    if isinstance(resolved, dict):
        return {
            key: resolve_template(item, input_data)
            for key, item in resolved.items()
        }

    if isinstance(resolved, list):
        return [resolve_template(item, input_data) for item in resolved]

    return resolved


def _call_json_endpoint(
    url: str,
    method: str,
    headers: dict[str, str],
    body: Any,
    timeout_seconds: float | None = None,
) -> dict:
    encoded_body = None
    request_headers = dict(headers)

    if method != "GET" and body is not None:
        encoded_body = json.dumps(body).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")

    request = urllib.request.Request(
        url,
        data=encoded_body,
        headers=request_headers,
        method=method,
    )

    with urllib.request.urlopen(
        request,
        timeout=_request_timeout(timeout_seconds, default=15),
    ) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return {
            "status": response.status,
            "headers": dict(response.headers.items()),
            "body": _parse_response_body(raw),
        }


def _request_timeout(value: float | None, default: int) -> float:
    if value is None:
        return float(default)

    return max(float(value), 0.001)


def _parse_response_body(raw: str) -> Any:
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def _append_query(url: str, params: dict[str, Any]) -> str:
    parsed = urllib.parse.urlsplit(url)
    existing = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = urllib.parse.urlencode([
        *existing,
        *[(key, value) for key, value in params.items() if value is not None],
    ])

    return urllib.parse.urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        query,
        parsed.fragment,
    ))


def _inject_api_key_header(
    config: dict,
    headers: dict[str, str],
    owner_user_id: str | None,
    provider: str | None,
) -> dict[str, str]:
    api_key = _resolve_api_key(
        config,
        default_ref=None,
        owner_user_id=owner_user_id,
        provider=provider,
    )
    api_key_header = str(config.get("api_key_header") or "").strip()

    if api_key and api_key_header:
        return {**headers, api_key_header: api_key}

    return headers


def _resolve_api_key(
    config: dict,
    default_ref: str | None,
    owner_user_id: str | None,
    provider: str | None,
) -> str | None:
    credential_key = get_credential_secret(
        credential_id=config.get("credential_id"),
        owner_user_id=owner_user_id,
        provider=provider,
    )

    if credential_key:
        return credential_key

    api_key = config.get("api_key")

    if api_key:
        return str(api_key)

    api_key_ref = config.get("api_key_ref") or default_ref

    if api_key_ref:
        return os.getenv(str(api_key_ref))

    return None


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    return parsed if parsed > 0 else default


def _extract_search_results(provider: str, response: Any, max_results: int) -> list[dict]:
    if provider == "brave" and isinstance(response, dict):
        items = response.get("web", {}).get("results", [])
        return [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("description"),
            }
            for item in items[:max_results]
            if isinstance(item, dict)
        ]

    if provider == "tavily" and isinstance(response, dict):
        items = response.get("results", [])
        return [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content"),
            }
            for item in items[:max_results]
            if isinstance(item, dict)
        ]

    if isinstance(response, dict):
        items = response.get("results") or response.get("items") or []
    elif isinstance(response, list):
        items = response
    else:
        items = []

    return [
        item if isinstance(item, dict) else {"content": str(item)}
        for item in items[:max_results]
    ]


def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted = {}

    for key, value in headers.items():
        clean_key = key.lower()

        if (
            clean_key in {"authorization", "x-api-key", "api-key"}
            or "token" in clean_key
            or "secret" in clean_key
            or "key" in clean_key
        ):
            redacted[key] = "***"
        else:
            redacted[key] = value

    return redacted
