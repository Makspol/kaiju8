from hmac import compare_digest
from typing import Any

from app.modules.workflows import repository as workflows_repository
from app.modules.workflows.service import run_workflow


HTTP_TRIGGER_TYPE = "http.trigger"
SECRET_QUERY_KEYS = {"secret", "token", "key"}
SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-kaiju8-trigger-secret",
}


class HttpTriggerError(Exception):
    def __init__(self, code: str, status_code: int):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


def run_http_trigger(
    path: str,
    method: str,
    body: Any,
    headers: dict[str, str] | None = None,
    query: dict[str, str] | None = None,
    provided_secret: str | None = None,
) -> dict:
    match = _find_trigger(path)
    workflow = match["workflow"]
    node = match["node"]
    config = node.get("config", {})

    _ensure_secret(config=config, provided_secret=provided_secret)

    execution = run_workflow(
        workflow_id=workflow["id"],
        input_json=_request_payload(
            path=path,
            method=method,
            body=body,
            headers=headers or {},
            query=query or {},
        ),
        owner_user_id=workflow["owner_user_id"],
        trigger_node_id=node["id"],
    )

    if execution is None:
        raise HttpTriggerError("workflow_not_found", 404)

    return execution


def _find_trigger(path: str) -> dict:
    normalized_path = _normalize_path(path)
    matches = []

    for workflow in workflows_repository.list_workflows():
        for node in _http_trigger_nodes(workflow):
            config = node.get("config", {})

            if config.get("enabled") is False:
                continue

            if _normalize_path(config.get("path")) == normalized_path:
                matches.append({
                    "workflow": workflow,
                    "node": node,
                })

    if not matches:
        raise HttpTriggerError("http_trigger_not_found", 404)

    if len(matches) > 1:
        raise HttpTriggerError("http_trigger_path_conflict", 409)

    return matches[0]


def _http_trigger_nodes(workflow: dict) -> list[dict]:
    graph = workflow.get("graph") or {}
    nodes = graph.get("nodes", [])

    return [
        node
        for node in nodes
        if isinstance(node, dict) and node.get("type") == HTTP_TRIGGER_TYPE
    ]


def _ensure_secret(config: dict, provided_secret: str | None) -> None:
    expected_secret = str(config.get("secret") or "").strip()

    if not expected_secret:
        raise HttpTriggerError("http_trigger_secret_not_configured", 403)

    provided_secret = str(provided_secret or "").strip()

    if not provided_secret or not compare_digest(expected_secret, provided_secret):
        raise HttpTriggerError("invalid_http_trigger_secret", 403)


def _request_payload(
    path: str,
    method: str,
    body: Any,
    headers: dict[str, str],
    query: dict[str, str],
) -> dict:
    if isinstance(body, dict):
        payload = dict(body)
    else:
        payload = {"body": body}

    payload["http"] = {
        "method": method.upper(),
        "trigger_path": _normalize_path(path),
        "query": _safe_query(query),
        "headers": _safe_headers(headers),
    }

    return payload


def _safe_query(query: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in query.items()
        if key.lower() not in SECRET_QUERY_KEYS
    }


def _safe_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key.lower(): ("***" if key.lower() in SENSITIVE_HEADER_NAMES else value)
        for key, value in headers.items()
    }


def _normalize_path(value: object) -> str:
    return str(value or "").strip().strip("/")
