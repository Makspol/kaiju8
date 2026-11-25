import pytest
from fastapi import HTTPException

from app.api.routes.workflows import (
    analyze_node_input_fields_route,
    create_workflow_route,
    delete_workflow_route,
    get_node_input_fields_route,
    get_workflow_route,
    list_workflows_route,
    run_workflow_route,
    update_workflow_route,
    validate_workflow_route,
)
from app.modules.users.service import create_user
from app.modules.workflows.service import (
    create_workflow,
    delete_workflow,
    get_workflow,
    list_workflows,
    run_workflow,
    update_workflow,
)
from app.schemas.workflows import (
    AnalyzeNodeInputFieldsRequest,
    CreateWorkflowRequest,
    RunWorkflowRequest,
    UpdateWorkflowRequest,
)


def test_create_workflow_for_user_sets_owner():
    user = create_user(email="owner@example.com", name="Owner")

    workflow = create_workflow(
        name="Owned workflow",
        owner_user_id=user["id"],
    )

    assert workflow["owner_user_id"] == user["id"]
    assert get_workflow(workflow["id"], owner_user_id=user["id"]) == workflow


def test_create_workflow_rejects_missing_owner():
    workflow = create_workflow(name="Missing owner", owner_user_id="missing-id")

    assert workflow is None


def test_list_workflows_is_scoped_to_owner():
    owner = create_user(email="owner@example.com", name="Owner")
    other_user = create_user(email="other@example.com", name="Other")

    owner_workflow = create_workflow(
        name="Owner workflow",
        owner_user_id=owner["id"],
    )
    create_workflow(
        name="Other workflow",
        owner_user_id=other_user["id"],
    )

    workflows = list_workflows(owner_user_id=owner["id"])

    assert [workflow["id"] for workflow in workflows] == [owner_workflow["id"]]


def test_get_update_and_run_workflow_are_scoped_to_owner():
    owner = create_user(email="owner@example.com", name="Owner")
    other_user = create_user(email="other@example.com", name="Other")
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

    workflow = create_workflow(
        name="Owner workflow",
        graph=graph,
        owner_user_id=owner["id"],
    )

    assert get_workflow(workflow["id"], owner_user_id=owner["id"]) is not None
    assert get_workflow(workflow["id"], owner_user_id=other_user["id"]) is None

    assert update_workflow(
        workflow_id=workflow["id"],
        payload={"name": "Blocked update"},
        owner_user_id=other_user["id"],
    ) is None

    updated = update_workflow(
        workflow_id=workflow["id"],
        payload={"name": "Allowed update"},
        owner_user_id=owner["id"],
    )

    assert updated["name"] == "Allowed update"
    assert run_workflow(
        workflow_id=workflow["id"],
        input_json={},
        owner_user_id=other_user["id"],
    ) is None
    assert run_workflow(
        workflow_id=workflow["id"],
        input_json={"message": "hi"},
        owner_user_id=owner["id"],
    )["status"] == "success"


def test_delete_workflow_is_scoped_to_owner():
    owner = create_user(email="owner@example.com", name="Owner")
    other_user = create_user(email="other@example.com", name="Other")
    workflow = create_workflow(
        name="Owner workflow",
        owner_user_id=owner["id"],
    )

    assert delete_workflow(
        workflow_id=workflow["id"],
        owner_user_id=other_user["id"],
    ) is False
    assert get_workflow(workflow["id"], owner_user_id=owner["id"]) is not None
    assert delete_workflow(
        workflow_id=workflow["id"],
        owner_user_id=owner["id"],
    ) is True
    assert get_workflow(workflow["id"], owner_user_id=owner["id"]) is None


def test_workflow_route_functions_use_current_user_scope():
    owner = create_user(email="owner@example.com", name="Owner")
    other_user = create_user(email="other@example.com", name="Other")

    workflow = create_workflow_route(
        payload=CreateWorkflowRequest(name="Route workflow"),
        current_user=owner,
    )

    assert list_workflows_route(current_user=owner)[0]["id"] == workflow["id"]
    assert get_workflow_route(
        workflow_id=workflow["id"],
        current_user=owner,
    )["id"] == workflow["id"]
    assert update_workflow_route(
        workflow_id=workflow["id"],
        payload=UpdateWorkflowRequest(name="Route workflow updated"),
        current_user=owner,
    )["name"] == "Route workflow updated"

    with pytest.raises(HTTPException):
        get_workflow_route(
            workflow_id=workflow["id"],
            current_user=other_user,
        )

    with pytest.raises(HTTPException):
        update_workflow_route(
            workflow_id=workflow["id"],
            payload=UpdateWorkflowRequest(name="Blocked route update"),
            current_user=other_user,
        )

    with pytest.raises(HTTPException):
        delete_workflow_route(
            workflow_id=workflow["id"],
            current_user=other_user,
        )

    assert delete_workflow_route(
        workflow_id=workflow["id"],
        current_user=owner,
    ) == {"deleted": True}
    assert list_workflows_route(current_user=owner) == []


def test_workflow_routes_use_bearer_auth_scheme_in_openapi():
    from app.main import app

    schema = app.openapi()

    assert "HTTPBearer" in schema["components"]["securitySchemes"]
    assert schema["paths"]["/workflows"]["get"]["security"] == [
        {"HTTPBearer": []}
    ]


def test_workflow_route_run_and_validate_use_current_user_scope():
    owner = create_user(email="owner@example.com", name="Owner")
    other_user = create_user(email="other@example.com", name="Other")
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

    workflow = create_workflow(
        name="Route run workflow",
        graph=graph,
        owner_user_id=owner["id"],
    )

    assert validate_workflow_route(
        workflow_id=workflow["id"],
        current_user=owner,
    )["valid"] is True
    assert run_workflow_route(
        workflow_id=workflow["id"],
        payload=RunWorkflowRequest(input={}),
        current_user=owner,
    )["status"] == "success"

    with pytest.raises(HTTPException):
        validate_workflow_route(
            workflow_id=workflow["id"],
            current_user=other_user,
        )

    with pytest.raises(HTTPException):
        run_workflow_route(
            workflow_id=workflow["id"],
            payload=RunWorkflowRequest(input={}),
            current_user=other_user,
        )


def test_workflow_route_input_fields_use_current_user_scope():
    owner = create_user(email="owner@example.com", name="Owner")
    other_user = create_user(email="other@example.com", name="Other")
    graph = {
        "nodes": [
            {
                "id": "start",
                "type": "manual.trigger",
                "config": {"test_payload": {"score": 90}},
            },
            {"id": "if", "type": "logic.if", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "if"},
        ],
        "settings": {"max_steps": 10},
    }

    workflow = create_workflow(
        name="Input fields workflow",
        graph=graph,
        owner_user_id=owner["id"],
    )

    result = get_node_input_fields_route(
        workflow_id=workflow["id"],
        node_id="if",
        current_user=owner,
    )

    assert result["fields"] == [
        {
            "path": "score",
            "type": "number",
            "source_node_id": "start",
            "source": "start",
        }
    ]

    with pytest.raises(HTTPException):
        get_node_input_fields_route(
            workflow_id=workflow["id"],
            node_id="if",
            current_user=other_user,
        )


def test_workflow_route_analyzes_draft_graph_input_fields():
    owner = create_user(email="owner@example.com", name="Owner")

    result = analyze_node_input_fields_route(
        payload=AnalyzeNodeInputFieldsRequest.model_validate({
            "node_id": "if",
            "graph": {
                "nodes": [
                    {
                        "id": "start",
                        "type": "manual.trigger",
                        "config": {"test_payload": {"email": "user@example.com"}},
                    },
                    {"id": "if", "type": "logic.if", "config": {}},
                ],
                "edges": [
                    {"source": "start", "target": "if"},
                ],
                "settings": {"max_steps": 10},
            },
        }),
        current_user=owner,
    )

    assert result["fields"] == [
        {
            "path": "email",
            "type": "string",
            "source_node_id": "start",
            "source": "start",
        }
    ]
