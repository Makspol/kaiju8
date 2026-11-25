from app.modules.workflows.validator import validate_graph


def test_valid_graph_passes_validation():
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

    result = validate_graph(graph)

    assert result["valid"] is True
    assert result["errors"] == []


def test_graph_without_trigger_fails_validation():
    graph = {
        "nodes": [
            {
                "id": "set",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "message", "value": "hello"},
                    ],
                },
            }
        ],
        "edges": [],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        error["field"] == "nodes"
        and "trigger" in error["message"].lower()
        for error in result["errors"]
    )


def test_unknown_node_type_fails_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {"id": "ghost", "type": "unknown.node", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "ghost"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        "Unknown node type" in error["message"]
        for error in result["errors"]
    )


def test_edge_to_missing_node_fails_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "missing"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        error["field"] == "edges[0].target"
        for error in result["errors"]
    )


def test_edge_to_trigger_fails_validation():
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
        ],
        "edges": [
            {"source": "start", "target": "set"},
            {"source": "set", "target": "start"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        error["field"] == "edges[1].target"
        and "does not accept incoming edges" in error["message"]
        for error in result["errors"]
    )


def test_invalid_edit_fields_config_fails_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {"id": "set", "type": "transform.edit_fields", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "set"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        "operations must be a non-empty list" in error["message"]
        for error in result["errors"]
    )


def test_invalid_reply_output_config_fails_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "reply",
                "type": "output.reply",
                "config": {
                    "mode": "field",
                    "field": "",
                    "include_data": "yes",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        "field is required" in error["message"]
        for error in result["errors"]
    )
    assert any(
        "include_data must be a boolean" in error["message"]
        for error in result["errors"]
    )


def test_invalid_if_comparison_values_fail_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "if",
                "type": "logic.if",
                "config": {
                    "field": "score",
                    "data_type": "number",
                    "operator": "gt",
                    "value": "high",
                },
            },
            {
                "id": "date_if",
                "type": "logic.if",
                "config": {
                    "field": "created_at",
                    "data_type": "date",
                    "operator": "between",
                    "value": "2026-01-01T00:00:00Z",
                },
            },
            {
                "id": "bool_if",
                "type": "logic.if",
                "config": {
                    "field": "approved",
                    "data_type": "boolean",
                    "operator": "equals",
                    "value": "maybe",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "if"},
            {"source": "if", "target": "date_if"},
            {"source": "date_if", "target": "bool_if"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        "value must be a number" in error["message"]
        for error in result["errors"]
    )
    assert any(
        "value_b is required for between" in error["message"]
        for error in result["errors"]
    )
    assert any(
        "value must be a boolean" in error["message"]
        for error in result["errors"]
    )


def test_standalone_ai_model_node_fails_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "agent",
                "type": "ai.claude",
                "config": {
                    "resource": "document",
                    "operation": "generate",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "agent"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        "Unknown node type: ai.claude" in error["message"]
        for error in result["errors"]
    )


def test_invalid_ai_agent_module_fails_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "agent",
                "type": "ai.agent",
                "config": {
                    "model": {"provider": "openai"},
                    "tools": [{"type": "database"}],
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "agent"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        "model.provider" in error["message"]
        for error in result["errors"]
    )
    assert any(
        "tools[0].type" in error["message"]
        for error in result["errors"]
    )


def test_invalid_ai_agent_visual_module_fails_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "agent",
                "type": "ai.agent",
                "config": {
                    "timeout_seconds": 0,
                    "modules": [
                        {
                            "id": "model-1",
                            "type": "ai.model.claude",
                            "port": "tools",
                            "config": {},
                        },
                        {
                            "id": "model-2",
                            "type": "ai.model.gemini",
                            "port": "model",
                            "config": {},
                        },
                        {
                            "id": "model-3",
                            "type": "ai.model.claude",
                            "port": "model",
                            "config": {},
                        },
                    ],
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "agent"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        "modules[0].port must be model" in error["message"]
        for error in result["errors"]
    )
    assert any(
        "model port accepts only one module" in error["message"]
        for error in result["errors"]
    )


def test_invalid_ai_node_limits_fail_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "agent",
                "type": "ai.agent",
                "config": {
                    "timeout_seconds": 0,
                    "modules": [
                        {
                            "id": "model-1",
                            "type": "ai.model.gemini",
                            "port": "model",
                            "config": {
                                "budget": -1,
                                "max_llm_calls": -1,
                                "max_tokens": 0,
                            },
                        },
                    ],
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "agent"},
        ],
        "settings": {"max_steps": 10},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        "model.budget must be a non-negative number" in error["message"]
        for error in result["errors"]
    )
    assert any(
        "model.max_llm_calls must be a non-negative integer" in error["message"]
        for error in result["errors"]
    )
    assert any(
        "model.max_tokens must be a positive integer" in error["message"]
        for error in result["errors"]
    )
    assert any(
        "timeout_seconds must be a positive number" in error["message"]
        for error in result["errors"]
    )


def test_invalid_max_steps_fails_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
        ],
        "edges": [],
        "settings": {"max_steps": 0},
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        error["field"] == "settings.max_steps"
        for error in result["errors"]
    )


def test_invalid_execution_limits_fail_validation():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
        ],
        "edges": [],
        "settings": {
            "max_steps": 10,
            "timeout_seconds": -1,
            "budget": -0.01,
            "max_llm_calls": -1,
            "max_tokens": 0,
            "ai_limits": {
                "claude": {
                    "budget": -1,
                    "max_llm_calls": -1,
                    "max_tokens": 0,
                },
                "gemini": [],
            },
        },
    }

    result = validate_graph(graph)

    assert result["valid"] is False
    assert any(
        error["field"] == "settings.timeout_seconds"
        for error in result["errors"]
    )
    assert any(
        error["field"] == "settings.budget"
        for error in result["errors"]
    )
    assert any(
        error["field"] == "settings.max_llm_calls"
        for error in result["errors"]
    )
    assert any(
        error["field"] == "settings.max_tokens"
        for error in result["errors"]
    )
    assert any(
        error["field"] == "settings.ai_limits.claude.budget"
        for error in result["errors"]
    )
    assert any(
        error["field"] == "settings.ai_limits.claude.max_llm_calls"
        for error in result["errors"]
    )
    assert any(
        error["field"] == "settings.ai_limits.claude.max_tokens"
        for error in result["errors"]
    )
    assert any(
        error["field"] == "settings.ai_limits.gemini"
        for error in result["errors"]
    )
