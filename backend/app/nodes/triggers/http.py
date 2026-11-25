from datetime import datetime, timezone

from app.nodes.base import TriggerNodeExecutor
from app.nodes.triggers.payload import (
    resolve_trigger_payload,
    validate_payload_config,
)
from app.runtime.types import ExecutionContext, NodeResult


class HttpTriggerNode(TriggerNodeExecutor):
    type = "http.trigger"
    label = "HTTP Trigger"
    description = "Starts workflow from an external HTTP request."
    config_schema = {
        "type": "object",
        "properties": {
            "enabled": {
                "type": "boolean",
                "default": True,
            },
            "path": {
                "type": "string",
                "default": "demo-webhook",
                "description": "Public path used as /http-triggers/{path}.",
            },
            "secret": {
                "type": "string",
                "default": "",
                "description": "Shared secret expected in X-Kaiju8-Trigger-Secret.",
            },
            "test_payload": {
                "type": "object",
                "default": {},
            },
        },
        "http_trigger": {
            "runner": "external",
            "endpoint": "/http-triggers/{path}",
            "secret_header": "X-Kaiju8-Trigger-Secret",
        },
    }
    config_ui = {
        "version": 1,
        "title": "HTTP webhook",
        "description": "Expose this workflow to external tools that can send JSON over HTTP.",
        "mode": "form",
        "fields": [
            {
                "key": "enabled",
                "label": "Enabled",
                "widget": "checkbox",
                "section": "basic",
                "default": True,
            },
            {
                "key": "path",
                "label": "Webhook path",
                "widget": "text",
                "section": "basic",
                "placeholder": "lead-created",
                "help": "Call POST /http-triggers/lead-created from an external service.",
            },
            {
                "key": "secret",
                "label": "Shared secret",
                "widget": "text",
                "section": "basic",
                "placeholder": "demo-secret",
                "help": "Send it in the X-Kaiju8-Trigger-Secret header.",
            },
            {
                "key": "test_payload",
                "label": "Test payload",
                "widget": "json",
                "section": "advanced",
                "default": {},
                "placeholder": "{\"event\":\"lead.created\"}",
            },
        ],
    }

    def validate_config(self, config: dict) -> list[str]:
        errors = []

        if "enabled" in config and not isinstance(config["enabled"], bool):
            errors.append("enabled must be a boolean.")

        path = config.get("path")

        if path is not None and not isinstance(path, str):
            errors.append("path must be a string.")
        elif isinstance(path, str) and path.strip() and not _valid_path(path):
            errors.append("path may contain letters, numbers, dashes, underscores, and slashes.")

        secret = config.get("secret")

        if secret is not None and not isinstance(secret, str):
            errors.append("secret must be a string.")

        errors.extend(validate_payload_config(config, "test_payload"))

        return errors

    def execute_trigger(
        self,
        config: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        payload = resolve_trigger_payload(
            config=config,
            initial_input=context.initial_input,
            default_key="test_payload",
        )
        http = payload.get("http")

        if not isinstance(http, dict):
            http = {}

        http.setdefault("trigger_path", _normalize_path(config.get("path")))
        http.setdefault("received_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

        return NodeResult(output={**payload, "http": http})


def _valid_path(value: str) -> bool:
    normalized = _normalize_path(value)

    if not normalized:
        return False

    return all(
        chunk.replace("-", "").replace("_", "").isalnum()
        for chunk in normalized.split("/")
    )


def _normalize_path(value: object) -> str:
    return str(value or "").strip().strip("/")
