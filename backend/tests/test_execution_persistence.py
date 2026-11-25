from app.modules.executions.service import (
    get_execution,
    list_execution_steps,
    list_executions,
)
from app.modules.workflows.service import create_workflow, run_workflow


def test_run_workflow_persists_execution():
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

    workflow = create_workflow(name="Persistent run", graph=graph)

    execution = run_workflow(workflow["id"], {"user": "Oleksii"})

    saved = get_execution(execution["id"])

    assert saved["id"] == execution["id"]
    assert saved["workflow_id"] == workflow["id"]
    assert saved["status"] == "success"
    assert saved["output"]["message"] == "hello"
    assert len(saved["steps"]) == 3


def test_list_execution_steps():
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

    workflow = create_workflow(name="Step list", graph=graph)

    execution = run_workflow(workflow["id"], {"hello": "world"})
    steps = list_execution_steps(execution["id"])

    assert len(steps) == 2
    assert steps[0]["node_id"] == "start"
    assert steps[1]["node_id"] == "reply"


def test_list_executions_returns_latest_runs_first():
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

    workflow = create_workflow(name="Run history", graph=graph)

    first = run_workflow(workflow["id"], {"run": 1})
    second = run_workflow(workflow["id"], {"run": 2})

    executions = list_executions(workflow["id"])

    assert [execution["id"] for execution in executions] == [
        second["id"],
        first["id"],
    ]
    assert executions[0]["input"]["run"] == 2


def test_invalid_workflow_run_persists_failed_execution():
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

    workflow = create_workflow(name="Invalid persistent run", graph=graph)

    execution = run_workflow(workflow["id"], {"user": "Oleksii"})
    saved = get_execution(execution["id"])

    assert execution["status"] == "failed"
    assert execution["error"] == "workflow_validation_failed"
    assert execution["validation"]["valid"] is False
    assert saved["status"] == "failed"
    assert saved["error"] == "workflow_validation_failed"
    assert saved["steps"] == []
