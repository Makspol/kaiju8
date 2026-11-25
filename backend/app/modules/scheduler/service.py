from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.scheduler import repository
from app.modules.scheduler.cron import next_cron_run, validate_cron_expression
from app.modules.workflows import repository as workflows_repository
from app.modules.workflows.service import run_workflow


SCHEDULE_TRIGGER_TYPE = "schedule.trigger"
DEFAULT_LOCK_SECONDS = 300


def sync_all_schedules(
    owner_user_id: str | None = None,
    now: datetime | None = None,
) -> dict:
    now = _ensure_aware(now or datetime.now(timezone.utc))
    workflows = workflows_repository.list_workflows(owner_user_id=owner_user_id)
    synced = []
    deactivated = 0

    for workflow in workflows:
        result = sync_workflow_schedules(workflow, now=now)
        synced.extend(result["schedules"])
        deactivated += result["deactivated"]

    return {
        "synced": len(synced),
        "deactivated": deactivated,
        "schedules": synced,
    }


def sync_workflow_schedules(
    workflow: dict,
    now: datetime | None = None,
) -> dict:
    now = _ensure_aware(now or datetime.now(timezone.utc))
    active_trigger_node_ids = set()
    synced = []

    for entry in _schedule_entries(workflow):
        active_trigger_node_ids.add(entry["trigger_node_id"])
        synced.append(
            repository.upsert_schedule(
                workflow_id=workflow["id"],
                owner_user_id=workflow["owner_user_id"],
                trigger_node_id=entry["trigger_node_id"],
                mode=entry["schedule"]["mode"],
                schedule=entry["schedule"],
                next_run_at=_next_run_at(entry["schedule"], now),
            )
        )

    deactivated = repository.deactivate_missing(
        workflow_id=workflow["id"],
        active_trigger_node_ids=active_trigger_node_ids,
    )

    return {
        "schedules": synced,
        "deactivated": deactivated,
    }


def list_schedules(owner_user_id: str | None = None) -> list[dict]:
    return repository.list_schedules(owner_user_id=owner_user_id)


def run_due_schedules(
    owner_user_id: str | None = None,
    now: datetime | None = None,
    limit: int = 20,
    lock_seconds: int = DEFAULT_LOCK_SECONDS,
    sync_first: bool = True,
) -> dict:
    now = _ensure_aware(now or datetime.now(timezone.utc))

    if sync_first:
        sync_all_schedules(owner_user_id=owner_user_id, now=now)

    claimed = repository.claim_due_schedules(
        now=now,
        lock_until=now + timedelta(seconds=lock_seconds),
        limit=max(limit, 1),
        owner_user_id=owner_user_id,
    )
    results = [
        _run_schedule(schedule=schedule, now=now)
        for schedule in claimed
    ]

    return {
        "claimed": len(claimed),
        "executed": len(results),
        "results": results,
    }


def run_schedule_now(
    schedule_id: str,
    owner_user_id: str | None = None,
    now: datetime | None = None,
) -> dict | None:
    schedule = repository.get_schedule(schedule_id)

    if schedule is None:
        return None

    if owner_user_id is not None and schedule["owner_user_id"] != owner_user_id:
        return None

    if schedule["status"] != repository.ACTIVE:
        return {
            "schedule": schedule,
            "execution": None,
            "error": "schedule_inactive",
        }

    return _run_schedule(
        schedule=schedule,
        now=_ensure_aware(now or datetime.now(timezone.utc)),
    )


def _run_schedule(schedule: dict, now: datetime) -> dict:
    workflow = workflows_repository.get_workflow(schedule["workflow_id"])
    definition = schedule["schedule"]
    next_run_at = _next_run_at(definition, now)

    if workflow is None:
        updated = repository.mark_failed(
            schedule_id=schedule["id"],
            last_run_at=now,
            next_run_at=next_run_at,
            error="workflow_not_found",
        )
        return {
            "schedule": updated,
            "execution": None,
            "error": "workflow_not_found",
        }

    input_json = _scheduled_input(
        schedule=schedule,
        definition=definition,
        now=now,
    )
    execution = run_workflow(
        workflow_id=workflow["id"],
        input_json=input_json,
        owner_user_id=workflow["owner_user_id"],
        trigger_node_id=schedule["trigger_node_id"],
    )
    execution_error = None

    if execution is None:
        execution_error = "workflow_not_found"
    elif execution.get("status") != "success":
        execution_error = execution.get("error") or execution.get("status")

    updated = repository.mark_completed(
        schedule_id=schedule["id"],
        last_run_at=now,
        next_run_at=next_run_at,
        execution_id=execution["id"] if execution else None,
        error=execution_error,
    )

    return {
        "schedule": updated,
        "execution": execution,
        "error": execution_error,
    }


def _schedule_entries(workflow: dict) -> list[dict]:
    graph = workflow.get("graph") or {}
    entries = []

    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue

        if node.get("type") != SCHEDULE_TRIGGER_TYPE:
            continue

        schedule = _schedule_from_config(node.get("config", {}))

        if schedule is None:
            continue

        entries.append({
            "trigger_node_id": node.get("id"),
            "schedule": schedule,
        })

    return [
        entry
        for entry in entries
        if entry["trigger_node_id"]
    ]


def _schedule_from_config(config: dict) -> dict | None:
    if not isinstance(config, dict):
        return None

    if config.get("enabled") is False:
        return None

    mode = str(config.get("mode") or "interval").lower()
    timezone_name = str(config.get("timezone") or "UTC").strip() or "UTC"

    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return None

    payload = _payload_from_config(config)
    schedule: dict[str, Any] = {
        "enabled": True,
        "mode": mode,
        "timezone": timezone_name,
        "payload": payload,
    }

    if mode == "interval":
        interval_seconds = _interval_seconds(config)

        if interval_seconds is None:
            return None

        schedule["interval_seconds"] = interval_seconds
        return schedule

    if mode == "cron":
        cron = str(config.get("cron") or "0 9 * * *").strip()

        if not validate_cron_expression(cron):
            return None

        schedule["cron"] = cron
        return schedule

    return None


def _next_run_at(schedule: dict, after: datetime) -> datetime:
    mode = schedule["mode"]
    timezone_name = schedule.get("timezone") or "UTC"

    if mode == "interval":
        return _ensure_aware(after) + timedelta(seconds=int(schedule["interval_seconds"]))

    if mode == "cron":
        return next_cron_run(
            expression=schedule["cron"],
            timezone_name=timezone_name,
            after=_ensure_aware(after),
        )

    raise ValueError(f"Unsupported schedule mode: {mode}")


def _scheduled_input(schedule: dict, definition: dict, now: datetime) -> dict:
    payload = dict(definition.get("payload") or {})
    scheduler_payload = payload.get("scheduler")

    if not isinstance(scheduler_payload, dict):
        scheduler_payload = {}

    payload.setdefault("scheduled_at", schedule.get("next_run_at") or now.isoformat())
    payload["scheduler"] = {
        **scheduler_payload,
        "schedule_id": schedule["id"],
        "workflow_id": schedule["workflow_id"],
        "trigger_node_id": schedule["trigger_node_id"],
    }

    return payload


def _payload_from_config(config: dict) -> dict:
    payload = config.get("payload")

    if isinstance(payload, dict):
        return dict(payload)

    test_payload = config.get("test_payload")

    if isinstance(test_payload, dict):
        return dict(test_payload)

    return {}


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


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)
