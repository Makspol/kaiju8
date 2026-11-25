from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.nodes.base import TriggerNodeExecutor
from app.modules.scheduler.cron import validate_cron_expression
from app.nodes.triggers.payload import (
    validate_payload_config,
)
from app.runtime.types import ExecutionContext, NodeResult


SCHEDULE_MODES = {"interval", "cron"}


class ScheduleTriggerNode(TriggerNodeExecutor):
    type = "schedule.trigger"
    label = "Schedule Trigger"
    description = "Starts workflow from a planned interval or cron schedule."
    config_schema = {
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "enum": sorted(SCHEDULE_MODES),
                "default": "interval",
            },
            "enabled": {
                "type": "boolean",
                "default": True,
            },
            "interval_seconds": {
                "type": "integer",
                "default": 3600,
                "minimum": 1,
            },
            "intervalSeconds": {
                "type": "integer",
                "default": 3600,
                "minimum": 1,
            },
            "cron": {
                "type": "string",
                "default": "0 9 * * *",
                "description": "Five-field cron expression: minute hour day month weekday.",
            },
            "timezone": {
                "type": "string",
                "default": "UTC",
            },
            "test_payload": {
                "type": "object",
                "default": {},
            },
            "payload": {
                "type": "object",
                "default": {},
                "description": "Payload used by the backend scheduler when the trigger fires.",
            },
        },
        "schedule": {
            "runner": "external",
            "description": (
                "The trigger describes when the workflow should run. A scheduler "
                "service can later call the normal workflow run endpoint."
            ),
        },
    }

    def validate_config(self, config: dict) -> list[str]:
        errors = []
        mode = _mode(config)

        if mode not in SCHEDULE_MODES:
            errors.append("mode must be interval or cron.")
        elif mode == "interval" and _interval_seconds(config) is None:
            errors.append("interval_seconds must be a positive integer.")
        elif mode == "cron" and not validate_cron_expression(config.get("cron", "0 9 * * *")):
            errors.append("cron must be a five-field cron expression.")

        if "enabled" in config and not isinstance(config["enabled"], bool):
            errors.append("enabled must be a boolean.")

        timezone_name = _timezone(config)

        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            errors.append("timezone must be a valid IANA timezone, for example UTC.")

        errors.extend(validate_payload_config(config, "test_payload"))
        errors.extend(validate_payload_config(config, "payload"))

        return errors

    def execute_trigger(
        self,
        config: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        payload = _resolve_schedule_payload(config=config, initial_input=context.initial_input)
        now = datetime.now(timezone.utc)
        timezone_name = _timezone(config)
        local_now = now.astimezone(ZoneInfo(timezone_name))
        mode = _mode(config)
        scheduled_at = (
            payload.get("scheduled_at")
            or payload.get("scheduledAt")
            or local_now.isoformat()
        )

        schedule = {
            "mode": mode,
            "timezone": timezone_name,
            "scheduled_at": scheduled_at,
            "fired_at": now.isoformat().replace("+00:00", "Z"),
        }

        if mode == "interval":
            schedule["interval_seconds"] = _interval_seconds(config)
        else:
            schedule["cron"] = str(config.get("cron", "0 9 * * *")).strip()

        return NodeResult(output={**payload, "schedule": schedule})


def _mode(config: dict) -> str:
    return str(config.get("mode") or "interval").lower()


def _interval_seconds(config: dict) -> int | None:
    value = config.get("interval_seconds", config.get("intervalSeconds", 3600))

    if isinstance(value, bool):
        return None

    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return None

    if seconds < 1:
        return None

    return seconds


def _timezone(config: dict) -> str:
    timezone_name = config.get("timezone") or "UTC"

    return str(timezone_name).strip() or "UTC"


def _resolve_schedule_payload(config: dict, initial_input: dict) -> dict:
    if initial_input:
        return dict(initial_input)

    payload = config.get("payload")

    if isinstance(payload, dict) and payload:
        return dict(payload)

    test_payload = config.get("test_payload")

    if isinstance(test_payload, dict):
        return dict(test_payload)

    return {}
