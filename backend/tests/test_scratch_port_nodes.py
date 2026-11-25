from app.runtime.engine import WorkflowEngine


def test_transform_nodes_can_clean_and_summarize_items():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "dedupe",
                "type": "transform.remove_duplicates",
                "config": {"field": "email"},
            },
            {
                "id": "summary",
                "type": "transform.summarize",
                "config": {"aggregation": "count", "output_field": "unique_count"},
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "dedupe"},
            {"source": "dedupe", "target": "summary"},
            {"source": "summary", "target": "reply"},
        ],
    }

    result = WorkflowEngine().execute(
        graph,
        {
            "items": [
                {"email": "first@example.com", "score": 10},
                {"email": "first@example.com", "score": 20},
                {"email": "second@example.com", "score": 30},
            ]
        },
    )

    assert result["status"] == "success"
    assert len(result["output"]["items"]) == 2
    assert result["output"]["removed_count"] == 1
    assert result["output"]["unique_count"] == 2


def test_condition_node_routes_to_matching_branch():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "condition",
                "type": "logic.condition",
                "config": {
                    "conditions": [
                        {
                            "field": "score",
                            "data_type": "number",
                            "operator": "gt",
                            "value": 70,
                        }
                    ]
                },
            },
            {
                "id": "passed",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "result", "value": "passed"},
                    ],
                },
            },
            {
                "id": "failed",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "result", "value": "failed"},
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "condition"},
            {"source": "condition", "target": "passed", "label": "true"},
            {"source": "condition", "target": "failed", "label": "false"},
            {"source": "passed", "target": "reply"},
            {"source": "failed", "target": "reply"},
        ],
    }

    result = WorkflowEngine().execute(graph, {"score": 90})

    assert result["status"] == "success"
    assert result["output"]["result"] == "passed"
    assert [step["node_id"] for step in result["steps"]] == [
        "start",
        "condition",
        "passed",
        "reply",
    ]


def test_if_node_routes_with_simple_number_condition():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "if",
                "type": "logic.if",
                "config": {
                    "field": "score",
                    "data_type": "number",
                    "operator": "gte",
                    "value": 80,
                },
            },
            {
                "id": "passed",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "result", "value": "passed"},
                    ],
                },
            },
            {
                "id": "failed",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "result", "value": "failed"},
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "if"},
            {"source": "if", "target": "passed", "label": "true"},
            {"source": "if", "target": "failed", "label": "false"},
            {"source": "passed", "target": "reply"},
            {"source": "failed", "target": "reply"},
        ],
    }

    result = WorkflowEngine().execute(graph, {"score": "80"})

    assert result["status"] == "success"
    assert result["output"]["route"] == "true"
    assert result["output"]["result"] == "passed"
    assert "score" in result["steps"][1]["output"]["_condition"]["input_fields"]


def test_if_node_string_and_date_comparisons():
    string_graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "if",
                "type": "logic.if",
                "config": {
                    "field": "message",
                    "data_type": "string",
                    "operator": "not_contains",
                    "value": "blocked",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "if"},
        ],
    }
    date_graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "if",
                "type": "logic.if",
                "config": {
                    "field": "created_at",
                    "data_type": "date",
                    "operator": "between",
                    "value": "2026-01-01T00:00:00Z",
                    "value_b": "2026-12-31T23:59:59Z",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "if"},
        ],
    }

    string_result = WorkflowEngine().execute(string_graph, {"message": "allowed text"})
    date_result = WorkflowEngine().execute(date_graph, {"created_at": "2026-05-23T10:00:00Z"})

    assert string_result["output"]["route"] == "true"
    assert date_result["output"]["route"] == "true"


def test_datetime_node_extracts_date_part():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "date",
                "type": "transform.datetime",
                "config": {
                    "operation": "extract_part",
                    "source_field": "created_at",
                    "part": "year",
                    "output_field": "created_year",
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "date"},
            {"source": "date", "target": "reply"},
        ],
    }

    result = WorkflowEngine().execute(graph, {"created_at": "2024-03-15T00:00:00Z"})

    assert result["status"] == "success"
    assert result["output"]["created_year"] == 2024


def test_http_request_node_resolves_templates_without_live_network_call():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "http",
                "type": "action.http_request",
                "config": {
                    "method": "POST",
                    "url": "https://example.com/{{resource}}",
                    "headers": {"Authorization": "Bearer {{token}}"},
                    "body": {"id": "{{id}}"},
                    "live": False,
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "http"},
            {"source": "http", "target": "reply"},
        ],
    }

    result = WorkflowEngine().execute(
        graph,
        {
            "resource": "users",
            "token": "secret",
            "id": 42,
        },
    )

    assert result["status"] == "success"
    assert result["output"]["url"] == "https://example.com/users"
    assert result["output"]["headers"]["Authorization"] == "***"
    assert result["output"]["body"] == {"id": 42}
    assert result["output"]["dry_run"] is True
