from datetime import datetime, timezone

from app.nodes.base import TriggerNodeExecutor
from app.nodes.triggers.payload import (
    resolve_trigger_payload,
    validate_payload_config,
)
from app.runtime.types import ExecutionContext, NodeResult


class ChatTriggerNode(TriggerNodeExecutor):
    type = "chat.trigger"
    label = "Chat Trigger"
    description = "Starts workflow when a chat message is sent."
    config_schema = {
        "type": "object",
        "properties": {
            "sample_message": {
                "type": "string",
                "default": "Hello",
            },
            "test_payload": {
                "type": "object",
                "default": {
                    "message": "Hello",
                },
            },
        },
    }

    def validate_config(self, config: dict) -> list[str]:
        errors = []
        sample_message = config.get("sample_message")

        if sample_message is not None and not isinstance(sample_message, str):
            errors.append("sample_message must be a string.")

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

        message = payload.get("message")

        if message is None:
            message = config.get("sample_message", "")
            payload["message"] = message

        payload.setdefault("conversation_id", "default")
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        return NodeResult(output=payload)
