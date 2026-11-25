from app.modules.workflows.field_analyzer import infer_node_input_fields


def test_field_analyzer_infers_if_inputs_without_running_workflow():
    graph = {
        "nodes": [
            {
                "id": "start",
                "type": "manual.trigger",
                "config": {
                    "test_payload": {
                        "user": {"name": "Jane"},
                        "score": 90,
                    },
                },
            },
            {
                "id": "edit",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "review.approved", "value": True},
                        {"operation": "set", "path": "review.note", "value": "{{ user.name }}"},
                    ],
                },
            },
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
        ],
        "edges": [
            {"source": "start", "target": "edit"},
            {"source": "edit", "target": "if"},
        ],
        "settings": {"max_steps": 10},
    }

    result = infer_node_input_fields(graph, "if")
    fields = {
        field["path"]: field["type"]
        for field in result["fields"]
    }

    assert fields["score"] == "number"
    assert fields["user.name"] == "string"
    assert fields["review.approved"] == "boolean"
    assert fields["review.note"] == "unknown"


def test_field_analyzer_infers_chat_trigger_defaults():
    graph = {
        "nodes": [
            {"id": "chat", "type": "chat.trigger", "config": {}},
            {"id": "if", "type": "logic.if", "config": {}},
        ],
        "edges": [
            {"source": "chat", "target": "if"},
        ],
        "settings": {"max_steps": 10},
    }

    result = infer_node_input_fields(graph, "if")
    fields = {
        field["path"]: field["type"]
        for field in result["fields"]
    }

    assert fields["message"] == "string"
    assert fields["conversation_id"] == "string"
    assert fields["timestamp"] == "date"


def test_field_analyzer_infers_schedule_trigger_defaults():
    graph = {
        "nodes": [
            {
                "id": "schedule",
                "type": "schedule.trigger",
                "config": {
                    "test_payload": {
                        "job": "daily-report",
                    },
                },
            },
            {"id": "if", "type": "logic.if", "config": {}},
        ],
        "edges": [
            {"source": "schedule", "target": "if"},
        ],
        "settings": {"max_steps": 10},
    }

    result = infer_node_input_fields(graph, "if")
    fields = {
        field["path"]: field["type"]
        for field in result["fields"]
    }

    assert fields["job"] == "string"
    assert fields["schedule.mode"] == "string"
    assert fields["schedule.scheduled_at"] == "date"
    assert fields["schedule.fired_at"] == "date"


def test_field_analyzer_uses_declared_workflow_input_fields():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {"id": "if", "type": "logic.if", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "if"},
        ],
        "settings": {
            "max_steps": 10,
            "input_fields": [
                {"path": "customer.email", "type": "string"},
                {"path": "total", "type": "number"},
            ],
        },
    }

    result = infer_node_input_fields(graph, "if")
    fields = {
        field["path"]: field["type"]
        for field in result["fields"]
    }

    assert fields == {
        "customer.email": "string",
        "total": "number",
    }
