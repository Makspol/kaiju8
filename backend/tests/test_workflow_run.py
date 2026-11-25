from app.modules.workflows.service import create_workflow, run_workflow


def test_run_saved_workflow():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "set",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "message", "value": "hello"},
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "set"},
            {"source": "set", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    workflow = create_workflow(name="Runnable workflow", graph=graph)

    result = run_workflow(workflow["id"], {"user": "Oleksii"})

    assert result["status"] == "success"
    assert result["output"]["user"] == "Oleksii"
    assert result["output"]["message"] == "hello"
    assert len(result["steps"]) == 3


def test_run_persists_usage_summary():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    workflow = create_workflow(name="Usage workflow", graph=graph)

    result = run_workflow(workflow["id"], {"user": "Jane"})

    assert result["status"] == "success"
    assert result["usage"] == {
        "llm_calls": 0,
        "tokens_used": 0,
        "budget_used": 0.0,
    }
    assert result["output"]["_usage"] == result["usage"]


def test_run_invalid_workflow_returns_validation_error():
    graph = {
        "nodes": [
            {
                "id": "set",
                "type": "transform.edit_fields",
                "config": {},
            },
        ],
        "edges": [],
        "settings": {"max_steps": 10},
    }

    workflow = create_workflow(name="Invalid workflow", graph=graph)

    result = run_workflow(workflow["id"], {})

    assert result["status"] == "failed"
    assert result["error"] == "workflow_validation_failed"
    assert result["validation"]["valid"] is False


def test_run_missing_workflow_returns_none():
    result = run_workflow("missing-id", {})

    assert result is None


def test_run_schedule_trigger_workflow():
    graph = {
        "nodes": [
            {
                "id": "schedule",
                "type": "schedule.trigger",
                "config": {
                    "mode": "cron",
                    "cron": "0 9 * * *",
                    "timezone": "UTC",
                    "test_payload": {
                        "job": "daily-lead-digest",
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

    workflow = create_workflow(name="Schedule workflow", graph=graph)

    result = run_workflow(workflow["id"], {})

    assert result["status"] == "success"
    assert result["output"]["job"] == "daily-lead-digest"
    assert result["output"]["schedule"]["mode"] == "cron"
    assert result["output"]["schedule"]["cron"] == "0 9 * * *"
    assert result["output"]["schedule"]["timezone"] == "UTC"
    assert result["output"]["schedule"]["scheduled_at"]
    assert result["output"]["schedule"]["fired_at"]


def test_run_workflow_can_start_from_specific_trigger():
    graph = {
        "nodes": [
            {
                "id": "manual",
                "type": "manual.trigger",
                "config": {
                    "test_payload": {
                        "source": "manual",
                    },
                },
            },
            {
                "id": "http",
                "type": "http.trigger",
                "config": {
                    "path": "lead-created",
                    "secret": "demo-secret",
                    "test_payload": {
                        "source": "http-test",
                    },
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "manual", "target": "reply"},
            {"source": "http", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    workflow = create_workflow(name="Multi-trigger workflow", graph=graph)

    result = run_workflow(
        workflow["id"],
        {"source": "webhook", "lead": {"email": "buyer@example.com"}},
        trigger_node_id="http",
    )

    assert result["status"] == "success"
    assert result["steps"][0]["node_id"] == "http"
    assert result["output"]["source"] == "webhook"
    assert result["output"]["lead"]["email"] == "buyer@example.com"
