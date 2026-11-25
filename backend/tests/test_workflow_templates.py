from app.api.routes.workflow_templates import list_workflow_templates_route
from app.modules.workflow_templates.service import list_workflow_templates
from app.modules.workflows.validator import validate_graph


def test_workflow_templates_are_valid_graphs():
    templates = list_workflow_templates()

    assert {template["id"] for template in templates} == {
        "refund_reply_chain",
        "ticket_router",
        "campaign_review",
        "launch_plan_workers",
    }
    assert [template["pattern"] for template in templates] == [
        "prompt_chaining",
        "routing",
        "parallelization",
        "orchestrator_worker",
    ]
    assert [template["name"] for template in templates] == [
        "Refund Reply Chain",
        "Ticket Router",
        "Campaign Review",
        "Launch Plan Workers",
    ]

    for template in templates:
        result = validate_graph(template["graph"])
        assert result["valid"], template["id"]


def test_workflow_templates_route_returns_public_templates():
    templates = list_workflow_templates_route()

    assert templates[0]["graph"]["nodes"]


def test_routing_template_has_one_router_and_three_specialist_branches():
    template = _template_by_id("ticket_router")
    graph = template["graph"]

    assert _node_types(graph) == {
        "in": "manual.trigger",
        "router": "ai.agent",
        "billing": "ai.agent",
        "technical": "ai.agent",
        "general": "ai.agent",
        "out": "output.reply",
    }
    assert _edge_routes(graph, "router") == {
        ("router", "billing", "billing"),
        ("router", "technical", "technical"),
        ("router", "general", "general"),
    }
    assert _incoming_sources(graph, "out") == {"billing", "technical", "general"}


def test_parallelization_template_fans_out_then_fans_in():
    template = _template_by_id("campaign_review")
    graph = template["graph"]

    assert _outgoing_targets(graph, "coordinator") == {
        "brand_review",
        "legal_review",
        "budget_review",
    }
    assert _incoming_sources(graph, "aggregate") == {
        "brand_review",
        "legal_review",
        "budget_review",
    }
    assert _outgoing_targets(graph, "aggregate") == {"out"}


def test_orchestrator_worker_template_fans_out_then_synthesizes():
    template = _template_by_id("launch_plan_workers")
    graph = template["graph"]

    assert _outgoing_targets(graph, "orchestrator") == {
        "research_worker",
        "message_worker",
        "risk_worker",
    }
    assert _incoming_sources(graph, "synthesizer") == {
        "research_worker",
        "message_worker",
        "risk_worker",
    }
    assert _outgoing_targets(graph, "synthesizer") == {"out"}


def _template_by_id(template_id: str) -> dict:
    return next(
        template
        for template in list_workflow_templates()
        if template["id"] == template_id
    )


def _node_types(graph: dict) -> dict[str, str]:
    return {
        node["id"]: node["type"]
        for node in graph["nodes"]
    }


def _outgoing_targets(graph: dict, source_id: str) -> set[str]:
    return {
        edge["target"]
        for edge in graph["edges"]
        if edge["source"] == source_id
    }


def _incoming_sources(graph: dict, target_id: str) -> set[str]:
    return {
        edge["source"]
        for edge in graph["edges"]
        if edge["target"] == target_id
    }


def _edge_routes(graph: dict, source_id: str) -> set[tuple[str, str, str | None]]:
    return {
        (edge["source"], edge["target"], edge.get("label") or edge.get("branch"))
        for edge in graph["edges"]
        if edge["source"] == source_id
    }
