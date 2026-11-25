from app.modules.workflows.service import (
    create_workflow,
    delete_workflow,
    get_workflow,
    list_workflows,
    run_workflow,
    update_workflow,
)


def test_create_workflow():
    workflow = create_workflow(name="Demo workflow")

    assert workflow["id"]
    assert workflow["owner_user_id"]
    assert workflow["name"] == "Demo workflow"
    assert workflow["graph"] == {
        "nodes": [],
        "edges": [],
        "settings": {"max_steps": 20},
    }


def test_get_workflow():
    workflow = create_workflow(name="Demo workflow")

    saved = get_workflow(workflow["id"])

    assert saved["id"] == workflow["id"]
    assert saved["name"] == "Demo workflow"


def test_list_workflows():
    workflow = create_workflow(name="Listed workflow")

    workflows = list_workflows()
    workflow_ids = {item["id"] for item in workflows}

    assert workflow["id"] in workflow_ids


def test_update_workflow_name_and_graph():
    workflow = create_workflow(name="Old name")

    new_graph = {
        "nodes": [{"id": "start", "type": "manual.trigger", "config": {}}],
        "edges": [],
        "settings": {"max_steps": 10},
    }

    updated = update_workflow(
        workflow["id"],
        {
            "name": "New name",
            "graph": new_graph,
        },
    )

    assert updated["name"] == "New name"
    assert updated["owner_user_id"] == workflow["owner_user_id"]
    assert updated["graph"] == new_graph


def test_create_workflow_with_missing_owner_returns_none():
    workflow = create_workflow(
        name="Missing owner",
        owner_user_id="missing-user-id",
    )

    assert workflow is None


def test_update_missing_workflow_returns_none():
    updated = update_workflow("missing-id", {"name": "Nope"})

    assert updated is None


def test_delete_workflow_removes_workflow_and_executions():
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
    workflow = create_workflow(name="Delete me", graph=graph)
    execution = run_workflow(workflow["id"], input_json={"message": "hello"})

    assert execution["id"]
    assert delete_workflow(workflow["id"]) is True
    assert get_workflow(workflow["id"]) is None
    assert delete_workflow(workflow["id"]) is False
