import json
import urllib.error
import urllib.request
from typing import Any

from app.nodes.base import NodeExecutor
from app.nodes.helpers import resolve_template
from app.runtime.types import ExecutionContext, NodeResult


class HttpRequestNode(NodeExecutor):
    type = "action.http_request"
    category = "action"
    label = "HTTP Request"
    description = "Sends a configurable HTTP request. Dry-run mode is used by default."
    config_schema = {
        "type": "object",
        "required": ["url"],
        "properties": {
            "method": {"type": "string"},
            "url": {"type": "string"},
            "headers": {},
            "body": {},
            "live": {"type": "boolean"},
        },
    }
    config_ui = {
        "version": 1,
        "title": "HTTP request",
        "description": "Call an external endpoint. Dry run is enabled by default for safer testing.",
        "mode": "form",
        "fields": [
            {
                "key": "method",
                "label": "Method",
                "widget": "select",
                "section": "basic",
                "default": "GET",
                "options": [
                    {"value": "GET", "label": "GET"},
                    {"value": "POST", "label": "POST"},
                    {"value": "PUT", "label": "PUT"},
                    {"value": "PATCH", "label": "PATCH"},
                    {"value": "DELETE", "label": "DELETE"},
                ],
            },
            {
                "key": "url",
                "label": "URL",
                "widget": "text",
                "section": "basic",
                "placeholder": "https://api.example.com/customers/{{ customer.id }}",
                "help": "Templates like {{ customer.id }} are resolved from workflow data.",
            },
            {
                "key": "live",
                "label": "Send real request",
                "widget": "checkbox",
                "section": "basic",
                "default": False,
                "help": "Keep off while testing to avoid accidental external calls.",
            },
            {
                "key": "headers",
                "label": "Headers",
                "widget": "json",
                "section": "advanced",
                "placeholder": "{\"Content-Type\":\"application/json\"}",
            },
            {
                "key": "body",
                "label": "Body",
                "widget": "json",
                "section": "advanced",
                "visible_when": {"field": "method", "in": ["POST", "PUT", "PATCH"]},
                "placeholder": "{\"name\":\"{{ customer.name }}\"}",
            },
        ],
    }

    def validate_config(self, config: dict) -> list[str]:
        errors = []
        method = str(config.get("method", "GET")).upper()
        url = config.get("url")

        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            errors.append("method must be GET, POST, PUT, PATCH, or DELETE.")

        if not isinstance(url, str) or not url.strip():
            errors.append("url is required.")

        return errors

    def execute(
        self,
        config: dict,
        input_data: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        method = str(config.get("method", "GET")).upper()
        url = str(resolve_template(config.get("url"), input_data)).strip()
        headers = _resolve_headers(config.get("headers"), input_data)
        body = _resolve_body(config.get("body"), input_data)
        live = bool(config.get("live", False))

        if not url.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://.")

        if live:
            response = _call_json_endpoint(url, method, headers, body)
            output = {
                "method": method,
                "url": url,
                "headers": _redact_headers(headers),
                "body": body,
                "live": True,
                "response": response,
            }
        else:
            output = {
                "method": method,
                "url": url,
                "headers": _redact_headers(headers),
                "body": body,
                "live": False,
                "dry_run": True,
                "response": {
                    "status": 200,
                    "json": {
                        "ok": True,
                        "mock": True,
                    },
                },
            }

        return NodeResult(output=output)


def _resolve_headers(value: Any, data: dict) -> dict[str, str]:
    headers = {}

    if isinstance(value, dict):
        items = value.items()
    elif isinstance(value, list):
        items = [
            (item.get("name"), item.get("value"))
            for item in value
            if isinstance(item, dict)
        ]
    else:
        items = []

    for key, raw_value in items:
        if not key:
            continue

        resolved = resolve_template(raw_value, data)
        headers[str(key)] = "" if resolved is None else str(resolved)

    return headers


def _resolve_body(value: Any, data: dict) -> Any:
    resolved = resolve_template(value, data)

    if isinstance(resolved, str):
        try:
            return json.loads(resolved)
        except ValueError:
            return resolved

    if isinstance(resolved, dict):
        return {
            key: resolve_template(item, data)
            for key, item in resolved.items()
        }

    if isinstance(resolved, list):
        return [resolve_template(item, data) for item in resolved]

    return resolved


def _call_json_endpoint(
    url: str,
    method: str,
    headers: dict[str, str],
    body: Any,
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

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return {
                "status": response.status,
                "headers": dict(response.headers.items()),
                "json": _parse_response_body(raw),
            }
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        return {
            "status": error.code,
            "headers": dict(error.headers.items()),
            "json": _parse_response_body(raw),
        }


def _parse_response_body(raw: str) -> Any:
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted = {}

    for key, value in headers.items():
        if key.lower() in {"authorization", "x-api-key", "api-key"}:
            redacted[key] = "***"
        else:
            redacted[key] = value

    return redacted
