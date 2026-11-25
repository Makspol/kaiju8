from app.nodes.base import TriggerNodeExecutor
from app.nodes.triggers.payload import (
    resolve_trigger_payload,
    validate_payload_config,
)
from app.runtime.types import ExecutionContext, NodeResult


class ManualTriggerNode(TriggerNodeExecutor):
    type = "manual.trigger"
    label = "Manual Trigger"
    description = "Starts workflow manually with optional test data."
    config_schema = {
        "type": "object",
        "properties": {
            "test_payload": {
                "type": "object",
                "default": {},
            },
        },
    }

    def validate_config(self, config: dict) -> list[str]:
        return validate_payload_config(config, "test_payload")

    def execute_trigger(
        self,
        config: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        return NodeResult(
            output=resolve_trigger_payload(
                config=config,
                initial_input=context.initial_input,
                default_key="test_payload",
            )
        )
