import pytest
from pydantic import ValidationError

from app.schemas.workflows import CreateWorkflowRequest


def test_create_workflow_request_rejects_invalid_graph_shape():
    with pytest.raises(ValidationError):
        CreateWorkflowRequest.model_validate(
            {
                "name": "Bad graph",
                "graph": {
                    "nodes": "not-a-list",
                    "edges": [],
                    "settings": {"max_steps": 10},
                },
            }
        )


def test_workflow_edges_preserve_route_labels():
    payload = CreateWorkflowRequest.model_validate(
        {
            "name": "Branch graph",
            "graph": {
                "nodes": [
                    {"id": "start", "type": "manual.trigger", "config": {}},
                    {"id": "if", "type": "logic.if", "config": {}},
                    {"id": "done", "type": "output.reply", "config": {}},
                ],
                "edges": [
                    {"source": "start", "target": "if"},
                    {"source": "if", "target": "done", "label": "true"},
                ],
                "settings": {"max_steps": 10},
            },
        }
    )

    assert payload.graph.model_dump()["edges"][1]["label"] == "true"
