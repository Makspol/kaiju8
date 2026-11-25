from datetime import datetime, timedelta, timezone

from app.modules.scheduler.service import (
    list_schedules,
    run_due_schedules,
    run_schedule_now,
    sync_all_schedules,
)
from app.modules.workflows.service import create_workflow, update_workflow


def test_scheduler_syncs_schedule_trigger():
    now = datetime(2026, 5, 23, 10, 0, tzinfo=timezone.utc)
    workflow = create_workflow(
        name="Scheduled workflow",
        graph=_schedule_graph(interval_seconds=60),
    )

    result = sync_all_schedules(now=now)

    assert result["synced"] == 1
    schedule = result["schedules"][0]
    assert schedule["workflow_id"] == workflow["id"]
    assert schedule["trigger_node_id"] == "schedule"
    assert schedule["status"] == "active"
    assert schedule["mode"] == "interval"
    assert schedule["next_run_at"] == (now + timedelta(seconds=60)).isoformat()


def test_scheduler_runs_due_schedule_and_advances_next_run():
    now = datetime(2026, 5, 23, 10, 0, tzinfo=timezone.utc)
    workflow = create_workflow(
        name="Due schedule",
        graph=_schedule_graph(interval_seconds=60),
    )

    sync_all_schedules(now=now)

    result = run_due_schedules(now=now + timedelta(seconds=60))

    assert result["claimed"] == 1
    assert result["executed"] == 1
    execution = result["results"][0]["execution"]
    schedule = result["results"][0]["schedule"]
    assert execution["status"] == "success"
    assert execution["workflow_id"] == workflow["id"]
    assert execution["output"]["job"] == "daily-report"
    assert execution["output"]["schedule"]["mode"] == "interval"
    assert execution["output"]["scheduler"]["schedule_id"] == schedule["id"]
    assert schedule["last_execution_id"] == execution["id"]
    assert schedule["next_run_at"] == (now + timedelta(seconds=120)).isoformat()


def test_scheduler_does_not_run_future_schedule():
    now = datetime(2026, 5, 23, 10, 0, tzinfo=timezone.utc)
    create_workflow(
        name="Future schedule",
        graph=_schedule_graph(interval_seconds=60),
    )

    sync_all_schedules(now=now)

    result = run_due_schedules(
        now=now + timedelta(seconds=59),
        sync_first=False,
    )

    assert result["claimed"] == 0
    assert result["executed"] == 0


def test_scheduler_can_run_schedule_now_for_manual_testing():
    now = datetime(2026, 5, 23, 10, 0, tzinfo=timezone.utc)
    workflow = create_workflow(
        name="Manual schedule run",
        graph=_schedule_graph(interval_seconds=3600),
    )
    sync_all_schedules(now=now)
    schedule = list_schedules()[0]

    result = run_schedule_now(
        schedule_id=schedule["id"],
        now=now + timedelta(minutes=5),
    )

    assert result["execution"]["status"] == "success"
    assert result["execution"]["workflow_id"] == workflow["id"]
    assert result["execution"]["output"]["job"] == "daily-report"
    assert result["schedule"]["last_execution_id"] == result["execution"]["id"]


def test_scheduler_deactivates_removed_schedule_trigger():
    workflow = create_workflow(
        name="Removed schedule",
        graph=_schedule_graph(interval_seconds=60),
    )
    sync_all_schedules()

    update_workflow(
        workflow_id=workflow["id"],
        payload={
            "graph": {
                "nodes": [
                    {"id": "start", "type": "manual.trigger", "config": {}},
                    {"id": "reply", "type": "output.reply", "config": {}},
                ],
                "edges": [{"source": "start", "target": "reply"}],
                "settings": {"max_steps": 10},
            }
        },
    )

    result = sync_all_schedules()
    schedules = list_schedules()

    assert result["deactivated"] == 1
    assert schedules[0]["status"] == "inactive"
    assert schedules[0]["next_run_at"] is None


def _schedule_graph(interval_seconds: int) -> dict:
    return {
        "nodes": [
            {
                "id": "schedule",
                "type": "schedule.trigger",
                "config": {
                    "mode": "interval",
                    "interval_seconds": interval_seconds,
                    "timezone": "UTC",
                    "payload": {
                        "job": "daily-report",
                    },
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "schedule", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }
