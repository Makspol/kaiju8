import asyncio

import pytest

from app.api.routes.http_triggers import run_http_trigger_route
from app.modules.http_triggers.service import HttpTriggerError, run_http_trigger
from app.modules.workflows.service import create_workflow


def test_http_trigger_runs_workflow_from_external_payload():
    workflow = create_workflow(
        name="Lead webhook",
        graph=_http_trigger_graph(),
    )

    result = run_http_trigger(
        path="lead-created",
        method="POST",
        body={
            "event": "lead.created",
            "lead": {
                "email": "buyer@example.com",
                "score": 91,
            },
        },
        headers={
            "X-Kaiju8-Trigger-Secret": "demo-secret",
            "Content-Type": "application/json",
        },
        query={
            "source": "crm",
            "secret": "demo-secret",
        },
        provided_secret="demo-secret",
    )

    assert result["workflow_id"] == workflow["id"]
    assert result["status"] == "success"
    assert result["steps"][0]["node_id"] == "http"
    assert result["steps"][0]["node_type"] == "http.trigger"
    assert result["output"]["event"] == "lead.created"
    assert result["output"]["lead"]["email"] == "buyer@example.com"
    assert result["output"]["http"]["method"] == "POST"
    assert result["output"]["http"]["trigger_path"] == "lead-created"
    assert result["output"]["http"]["query"] == {"source": "crm"}
    assert result["output"]["http"]["headers"]["x-kaiju8-trigger-secret"] == "***"


def test_http_trigger_rejects_wrong_secret():
    create_workflow(
        name="Lead webhook",
        graph=_http_trigger_graph(),
    )

    with pytest.raises(HttpTriggerError) as error:
        run_http_trigger(
            path="lead-created",
            method="POST",
            body={"event": "lead.created"},
            provided_secret="wrong",
        )

    assert error.value.code == "invalid_http_trigger_secret"
    assert error.value.status_code == 403


def test_http_trigger_route_runs_public_webhook():
    create_workflow(
        name="Lead webhook",
        graph=_http_trigger_graph(),
    )

    result = asyncio.run(
        run_http_trigger_route(
            path="lead-created",
            request=FakeRequest(
                method="POST",
                body={"event": "lead.created"},
                headers={"X-Kaiju8-Trigger-Secret": "demo-secret"},
            ),
            x_kaiju8_trigger_secret="demo-secret",
            secret=None,
        )
    )

    assert result["status"] == "success"
    assert result["output"]["event"] == "lead.created"


class FakeRequest:
    def __init__(
        self,
        method: str,
        body: dict,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
    ):
        self.method = method
        self._body = body
        self.headers = headers or {}
        self.query_params = query_params or {}

    async def json(self):
        return self._body

    async def body(self):
        return b""


def _http_trigger_graph() -> dict:
    return {
        "nodes": [
            {
                "id": "http",
                "type": "http.trigger",
                "config": {
                    "enabled": True,
                    "path": "lead-created",
                    "secret": "demo-secret",
                    "test_payload": {
                        "event": "lead.created",
                    },
                },
            },
            {"id": "reply", "type": "output.reply", "config": {"mode": "passthrough"}},
        ],
        "edges": [
            {"source": "http", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }
