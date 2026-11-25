from app.modules.node_catalog.service import (
    list_ai_agent_module_types,
    list_node_types,
)


def test_node_catalog_contains_basic_nodes():
    node_types = list_node_types()
    types = {node["type"] for node in node_types}

    assert "manual.trigger" in types
    assert "chat.trigger" in types
    assert "schedule.trigger" in types
    assert "http.trigger" in types
    assert "ai.agent" in types
    assert "ai.claude" not in types
    assert "ai.gemini" not in types
    assert "transform.edit_fields" in types
    assert "transform.datetime" in types
    assert "transform.remove_duplicates" in types
    assert "transform.summarize" in types
    assert "logic.condition" in types
    assert "logic.if" in types
    assert "action.http_request" in types
    assert "output.reply" in types


def test_node_catalog_marks_trigger_as_output_only():
    node_types = list_node_types()
    manual_trigger = next(node for node in node_types if node["type"] == "manual.trigger")
    chat_trigger = next(node for node in node_types if node["type"] == "chat.trigger")
    schedule_trigger = next(node for node in node_types if node["type"] == "schedule.trigger")
    http_trigger = next(node for node in node_types if node["type"] == "http.trigger")
    edit_fields = next(node for node in node_types if node["type"] == "transform.edit_fields")

    assert manual_trigger["ports"] == {"input": False, "output": True}
    assert chat_trigger["ports"] == {"input": False, "output": True}
    assert schedule_trigger["ports"] == {"input": False, "output": True}
    assert http_trigger["ports"] == {"input": False, "output": True}
    assert edit_fields["ports"] == {"input": True, "output": True}
    assert edit_fields["label"] == "Data Editor"


def test_node_catalog_contains_ai_group_after_triggers():
    node_types = list_node_types()
    types = [node["type"] for node in node_types]

    assert types[:5] == [
        "manual.trigger",
        "chat.trigger",
        "schedule.trigger",
        "http.trigger",
        "ai.agent",
    ]


def test_node_catalog_exposes_http_trigger_config():
    node_types = list_node_types()
    trigger = next(node for node in node_types if node["type"] == "http.trigger")
    schema = trigger["config_schema"]

    assert trigger["category"] == "trigger"
    assert schema["http_trigger"] == {
        "runner": "external",
        "endpoint": "/http-triggers/{path}",
        "secret_header": "X-Kaiju8-Trigger-Secret",
    }
    assert trigger["config_ui"]["mode"] == "form"
    assert [field["key"] for field in trigger["config_ui"]["fields"][:3]] == [
        "enabled",
        "path",
        "secret",
    ]


def test_node_catalog_exposes_schedule_trigger_config():
    node_types = list_node_types()
    schedule = next(node for node in node_types if node["type"] == "schedule.trigger")
    schema = schedule["config_schema"]

    assert schedule["category"] == "trigger"
    assert schema["properties"]["mode"]["enum"] == ["cron", "interval"]
    assert schema["properties"]["interval_seconds"]["default"] == 3600
    assert schema["properties"]["cron"]["default"] == "0 9 * * *"
    assert schema["properties"]["timezone"]["default"] == "UTC"
    assert schema["schedule"]["runner"] == "external"


def test_node_catalog_exposes_if_operator_metadata():
    node_types = list_node_types()
    if_node = next(node for node in node_types if node["type"] == "logic.if")
    schema = if_node["config_schema"]

    assert schema["field_source"]["kind"] == "upstream_fields"
    assert schema["properties"]["field"]["x-input-field"] is True
    assert "contains" in schema["operators_by_data_type"]["string"]
    assert "gte" in schema["operators_by_data_type"]["number"]
    assert "on_or_before" in schema["operators_by_data_type"]["date"]
    number_gte = next(
        spec
        for spec in schema["operator_specs_by_data_type"]["number"]
        if spec["operator"] == "gte"
    )
    date_between = next(
        spec
        for spec in schema["operator_specs_by_data_type"]["date"]
        if spec["operator"] == "between"
    )
    is_empty = next(
        spec
        for spec in schema["operator_specs_by_data_type"]["string"]
        if spec["operator"] == "is_empty"
    )

    assert number_gte["values"] == [
        {
            "name": "value",
            "label": "Value",
            "value_type": "number",
            "required": True,
        }
    ]
    assert [value["name"] for value in date_between["values"]] == ["value", "value_b"]
    assert is_empty["values"] == []
    assert if_node["config_ui"]["component"] == "condition_builder"
    assert if_node["config_ui"]["fields"][0]["widget"] == "field_path"


def test_node_catalog_exposes_reply_output_modes():
    node_types = list_node_types()
    reply = next(node for node in node_types if node["type"] == "output.reply")
    schema = reply["config_schema"]

    assert schema["properties"]["mode"]["enum"] == [
        "auto",
        "static",
        "field",
        "template",
        "passthrough",
    ]
    assert schema["properties"]["field"]["x-input-field"] is True
    assert schema["field_source"]["kind"] == "input_json"
    assert schema["reply_modes"]["template"]
    assert reply["config_ui"]["mode"] == "form"
    assert reply["config_ui"]["fields"][0]["key"] == "mode"
    assert any(
        field["key"] == "template"
        for field in reply["config_ui"]["fields"]
    )


def test_node_catalog_exposes_user_friendly_config_ui():
    node_types = list_node_types()
    http = next(node for node in node_types if node["type"] == "action.http_request")
    edit_fields = next(node for node in node_types if node["type"] == "transform.edit_fields")
    summarize = next(node for node in node_types if node["type"] == "transform.summarize")

    assert http["config_ui"]["mode"] == "form"
    assert [field["key"] for field in http["config_ui"]["fields"][:3]] == [
        "method",
        "url",
        "live",
    ]
    assert edit_fields["config_ui"]["component"] == "edit_fields_builder"
    assert summarize["config_ui"]["fields"][0]["key"] == "aggregation"


def test_node_catalog_exposes_ai_agent_modules():
    node_types = list_node_types()
    ai_agent = next(node for node in node_types if node["type"] == "ai.agent")
    schema = ai_agent["config_schema"]

    assert schema["module_port_layout"]["top"] == ["knowledge"]
    assert schema["module_port_layout"]["bottom"] == ["model", "memory", "tools"]
    assert schema["module_storage"] == {
        "strategy": "node_config_modules",
        "path": "config.modules",
        "description": "Visual AI Agent modules are stored inside the ai.agent node config.",
    }
    assert schema["module_ports"] == [
        {
            "id": "knowledge",
            "position": "top",
            "label": "Knowledge",
            "description": "Files and facts the AI Agent can use without user input.",
            "required": False,
            "multiple": True,
            "allowed_module_types": ["ai.knowledge.file"],
        },
        {
            "id": "model",
            "position": "bottom",
            "label": "Model",
            "description": "Model provider used by the AI Agent.",
            "required": True,
            "multiple": False,
            "allowed_module_types": ["ai.model.claude", "ai.model.gemini"],
        },
        {
            "id": "memory",
            "position": "bottom",
            "label": "Memory",
            "description": "Conversation history available to the AI Agent.",
            "required": False,
            "multiple": False,
            "allowed_module_types": ["ai.memory.basic", "ai.memory.file"],
        },
        {
            "id": "tools",
            "position": "bottom",
            "label": "Tools",
            "description": "External tools the AI Agent can call.",
            "required": False,
            "multiple": True,
            "allowed_module_types": [
                "ai.tool.http_request",
                "ai.tool.external_api",
                "ai.tool.web_search",
            ],
        },
    ]
    assert schema["supported_models"] == ["claude", "gemini"]
    assert schema["supported_tools"] == ["http_request", "web_search"]
    assert schema["properties"]["model"]["default"] == {"provider": "claude"}
    assert schema["properties"]["model"]["properties"]["budget"]["type"] == "number"
    assert schema["properties"]["model"]["properties"]["max_llm_calls"]["type"] == "integer"
    assert schema["properties"]["model"]["properties"]["max_tokens"]["type"] == "integer"
    assert schema["properties"]["memory"]["default"] == {"enabled": True}


def test_ai_agent_module_catalog_lists_attachable_modules():
    modules = list_ai_agent_module_types()
    module_types = {module["type"] for module in modules}

    assert module_types == {
        "ai.model.claude",
        "ai.model.gemini",
        "ai.memory.basic",
        "ai.memory.file",
        "ai.tool.http_request",
        "ai.tool.external_api",
        "ai.tool.web_search",
        "ai.knowledge.file",
    }
    assert all(module["category"] == "ai_agent_module" for module in modules)
    assert all(module["ports"] == {"input": False, "output": False} for module in modules)
    assert all(module["attachable_to"]["node_type"] == "ai.agent" for module in modules)
    assert all(module["attachable_to"]["position"] in {"top", "bottom"} for module in modules)


def test_ai_agent_module_catalog_filters_by_port():
    model_modules = list_ai_agent_module_types(port="model")
    memory_modules = list_ai_agent_module_types(port="memory")
    tool_modules = list_ai_agent_module_types(port="tools")

    assert [module["type"] for module in model_modules] == [
        "ai.model.claude",
        "ai.model.gemini",
    ]
    assert [module["type"] for module in memory_modules] == [
        "ai.memory.basic",
        "ai.memory.file",
    ]
    assert [module["type"] for module in tool_modules] == [
        "ai.tool.http_request",
        "ai.tool.external_api",
        "ai.tool.web_search",
    ]
