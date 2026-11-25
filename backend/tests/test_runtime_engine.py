from app.runtime.engine import WorkflowEngine


def test_runtime_executes_linear_workflow():
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

    engine = WorkflowEngine()

    result = engine.execute(graph, {"input": "test"})

    assert result["status"] == "success"
    assert result["output"]["message"] == "hello"
    assert len(result["steps"]) == 3
    assert result["steps"][0]["input"] == {}
    assert result["steps"][0]["output"] == {"input": "test"}
    assert [step["node_id"] for step in result["steps"]] == [
        "start",
        "set",
        "reply",
    ]


def test_manual_trigger_uses_test_payload_when_run_input_is_empty():
    graph = {
        "nodes": [
            {
                "id": "start",
                "type": "manual.trigger",
                "config": {"test_payload": {"message": "from test payload"}},
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {})

    assert result["status"] == "success"
    assert result["output"]["message"] == "from test payload"
    assert result["steps"][0]["output"] == {"message": "from test payload"}


def test_runtime_fans_out_and_waits_for_fan_in():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "brand",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "reviews.brand", "value": "ok"},
                    ],
                },
            },
            {
                "id": "legal",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "reviews.legal", "value": "check"},
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {"mode": "passthrough"}},
        ],
        "edges": [
            {"source": "start", "target": "brand"},
            {"source": "start", "target": "legal"},
            {"source": "brand", "target": "reply"},
            {"source": "legal", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"campaign": "spring"})

    assert result["status"] == "success"
    assert result["output"]["campaign"] == "spring"
    assert result["output"]["reviews"] == {
        "brand": "ok",
        "legal": "check",
    }
    assert result["output"]["_branches"]["brand"]["reviews"]["brand"] == "ok"
    assert result["output"]["_branches"]["legal"]["reviews"]["legal"] == "check"
    assert [step["node_id"] for step in result["steps"]] == [
        "start",
        "brand",
        "legal",
        "reply",
    ]


def test_runtime_routes_labeled_edges_to_one_branch():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "router",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "route", "value": "billing"},
                    ],
                },
            },
            {
                "id": "billing",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "handler", "value": "billing"},
                    ],
                },
            },
            {
                "id": "general",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "handler", "value": "general"},
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {"mode": "passthrough"}},
        ],
        "edges": [
            {"source": "start", "target": "router"},
            {"source": "router", "target": "billing", "label": "billing"},
            {"source": "router", "target": "general", "label": "general"},
            {"source": "billing", "target": "reply"},
            {"source": "general", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"ticket": {"category": "billing"}})

    assert result["status"] == "success"
    assert result["output"]["handler"] == "billing"
    assert [step["node_id"] for step in result["steps"]] == [
        "start",
        "router",
        "billing",
        "reply",
    ]


def test_chat_trigger_returns_chat_reply_from_output_node():
    graph = {
        "nodes": [
            {"id": "chat", "type": "chat.trigger", "config": {}},
            {
                "id": "set",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {
                            "operation": "set",
                            "path": "response",
                            "value": "Hello from workflow",
                        },
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "chat", "target": "set"},
            {"source": "set", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(
        graph,
        {
            "message": "hello",
            "conversation_id": "chat-1",
        },
    )

    assert result["status"] == "success"
    assert result["steps"][0]["output"]["message"] == "hello"
    assert result["steps"][0]["output"]["conversation_id"] == "chat-1"
    assert "timestamp" in result["steps"][0]["output"]
    assert result["output"]["response"] == "Hello from workflow"
    assert result["output"]["chat"] == {
        "reply": "Hello from workflow",
        "trigger_node_id": "chat",
    }


def test_chat_trigger_returns_ai_agent_response_from_output_node():
    graph = {
        "nodes": [
            {"id": "chat", "type": "chat.trigger", "config": {}},
            {
                "id": "agent",
                "type": "ai.agent",
                "config": {
                    "model": {
                        "provider": "gemini",
                        "api_key_ref": "MISSING_GEMINI_API_KEY",
                    },
                    "prompt": "Answer shortly",
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "chat", "target": "agent"},
            {"source": "agent", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"message": "hello"})

    assert result["status"] == "success"
    assert result["output"]["ai"]["status"] == "missing_api_key"
    assert result["output"]["chat"] == {
        "reply": result["output"]["ai"]["error"],
        "trigger_node_id": "chat",
    }
    assert result["output"]["response"] == result["output"]["ai"]["error"]


def test_reply_output_can_use_nested_response_field():
    graph = {
        "nodes": [
            {"id": "chat", "type": "chat.trigger", "config": {}},
            {
                "id": "edit",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {
                            "operation": "set",
                            "path": "ai.response",
                            "value": "Nested AI answer",
                        },
                    ],
                },
            },
            {
                "id": "reply",
                "type": "output.reply",
                "config": {"response_field": "ai.response"},
            },
        ],
        "edges": [
            {"source": "chat", "target": "edit"},
            {"source": "edit", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"message": "hello"})

    assert result["status"] == "success"
    assert result["output"]["response"] == "Nested AI answer"
    assert result["output"]["chat"]["reply"] == "Nested AI answer"


def test_reply_output_static_mode_can_return_manual_text_with_data():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "reply",
                "type": "output.reply",
                "config": {
                    "mode": "static",
                    "text": "Good",
                    "include_data": True,
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"score": 90})

    assert result["status"] == "success"
    assert result["output"] == {
        "response": "Good",
        "data": {"score": 90},
    }


def test_reply_output_field_mode_reads_nested_input_field():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "reply",
                "type": "output.reply",
                "config": {
                    "mode": "field",
                    "field": "review.message",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(
        graph,
        {"review": {"message": "Looks good"}},
    )

    assert result["status"] == "success"
    assert result["output"] == {"response": "Looks good"}


def test_reply_output_template_mode_resolves_input_fields():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "reply",
                "type": "output.reply",
                "config": {
                    "mode": "template",
                    "template": "Hello {{ user.name }}, status is {{ result.status }}.",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(
        graph,
        {
            "user": {"name": "Jane"},
            "result": {"status": "approved"},
        },
    )

    assert result["status"] == "success"
    assert result["output"] == {"response": "Hello Jane, status is approved."}


def test_chat_reply_uses_explicit_template_response():
    graph = {
        "nodes": [
            {"id": "chat", "type": "chat.trigger", "config": {}},
            {
                "id": "reply",
                "type": "output.reply",
                "config": {
                    "mode": "template",
                    "template": "Received: {{ message }}",
                },
            },
        ],
        "edges": [
            {"source": "chat", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"message": "hello"})

    assert result["status"] == "success"
    assert result["output"]["response"] == "Received: hello"
    assert result["output"]["chat"] == {
        "reply": "Received: hello",
        "trigger_node_id": "chat",
    }


def test_non_chat_trigger_does_not_add_chat_reply():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {"id": "reply", "type": "output.reply", "config": {"response": "ok"}},
        ],
        "edges": [
            {"source": "start", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {})

    assert result["status"] == "success"
    assert result["output"] == {"response": "ok"}


def test_runtime_stops_when_max_steps_exceeded():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "set",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {"operation": "set", "path": "message", "value": "loop"},
                    ],
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "set"},
            {"source": "set", "target": "start"},
        ],
        "settings": {"max_steps": 2},
    }

    engine = WorkflowEngine()

    result = engine.execute(graph, {})

    assert result["status"] == "failed"
    assert result["error"] == "max_steps_exceeded"
    assert len(result["steps"]) == 2


def test_runtime_edit_fields_adds_updates_and_removes_nested_fields():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "edit",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {
                            "operation": "set",
                            "path": "review.approved",
                            "value": False,
                        },
                        {
                            "operation": "add",
                            "path": "review.author",
                            "value": "{{ user.name }}",
                        },
                        {
                            "operation": "remove",
                            "path": "draft",
                        },
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "edit"},
            {"source": "edit", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(
        graph,
        {
            "user": {"name": "Jane"},
            "draft": "remove me",
            "review": {"author": "existing"},
        },
    )

    assert result["status"] == "success"
    assert result["output"]["review"] == {
        "approved": False,
        "author": "existing",
    }
    assert "draft" not in result["output"]


def test_runtime_edit_fields_can_add_empty_field():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "edit",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {
                            "operation": "add",
                            "path": "optionalNote",
                        },
                    ],
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "edit"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {})

    assert result["status"] == "success"
    assert result["output"]["optionalNote"] == ""


def test_runtime_edit_fields_ignores_blank_draft_operations():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "edit",
                "type": "transform.edit_fields",
                "config": {
                    "operations": [
                        {
                            "operation": "set",
                            "path": "isCorrect",
                            "value": True,
                        },
                        {
                            "operation": "add",
                            "path": "",
                            "value": "",
                        },
                    ],
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "edit"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"message": "hi"})

    assert result["status"] == "success"
    assert result["steps"][1]["input"] == {"message": "hi"}
    assert result["steps"][1]["output"] == {
        "message": "hi",
        "isCorrect": True,
    }


def test_runtime_executes_ai_agent_with_modules():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "agent",
                "type": "ai.agent",
                "config": {
                    "prompt": "Answer with context",
                    "model": {"provider": "gemini", "api_key_ref": "MISSING_GEMINI_API_KEY"},
                    "memory": {
                        "enabled": True,
                        "history": [
                            {"role": "user", "content": "Hello"},
                            {"role": "assistant", "content": "Hi"},
                        ],
                    },
                    "tools": [
                        {
                            "type": "http_request",
                            "config": {"method": "GET", "url": "https://example.com"},
                        }
                    ],
                    "knowledge": [
                        {"name": "facts.txt", "content": "Project facts."}
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "agent"},
            {"source": "agent", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"question": "What do we know?"})

    assert result["status"] == "success"
    assert result["output"]["question"] == "What do we know?"
    assert result["output"]["ai"]["kind"] == "agent"
    assert result["output"]["ai"]["provider"] == "gemini"
    assert result["output"]["ai"]["model"]["api_key_configured"] is True
    assert result["output"]["ai"]["memory"]["enabled"] is True
    assert result["output"]["ai"]["tools"][0]["type"] == "http_request"
    assert result["output"]["ai"]["knowledge"][0]["name"] == "facts.txt"
    assert result["output"]["ai"]["status"] == "missing_api_key"


def test_runtime_executes_ai_agent_with_visual_module_config():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "agent",
                "type": "ai.agent",
                "config": {
                    "modules": [
                        {
                            "id": "model-1",
                            "type": "ai.model.gemini",
                            "port": "model",
                            "config": {"api_key_ref": "MISSING_GEMINI_API_KEY"},
                        },
                        {
                            "id": "memory-1",
                            "type": "ai.memory.basic",
                            "port": "memory",
                            "config": {"enabled": True, "history": []},
                        },
                        {
                            "id": "tool-1",
                            "type": "ai.tool.http_request",
                            "port": "tools",
                            "config": {"method": "GET", "url": "https://example.com"},
                        },
                        {
                            "id": "tool-2",
                            "type": "ai.tool.external_api",
                            "port": "tools",
                            "config": {"method": "POST", "url": "https://api.example.com/leads"},
                        },
                        {
                            "id": "tool-3",
                            "type": "ai.tool.web_search",
                            "port": "tools",
                            "config": {"provider": "brave", "query": "{{ question }}"},
                        },
                        {
                            "id": "knowledge-1",
                            "type": "ai.knowledge.file",
                            "port": "knowledge",
                            "config": {
                                "name": "facts.txt",
                                "content": "Known facts.",
                                "reference": "knowledge://item-1",
                            },
                        },
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "agent"},
            {"source": "agent", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"question": "What do we know?"})

    assert result["status"] == "success"
    assert result["output"]["ai"]["provider"] == "gemini"
    assert result["output"]["ai"]["model"]["api_key_configured"] is True
    assert result["output"]["ai"]["tools"] == [
        {
            "type": "http_request",
            "config": {"method": "GET", "url": "https://example.com"},
        },
        {
            "type": "http_request",
            "config": {"method": "POST", "url": "https://api.example.com/leads"},
        },
        {
            "type": "web_search",
            "config": {"provider": "brave", "query": "{{ question }}"},
        },
    ]
    assert result["output"]["ai"]["knowledge"] == [
        {
            "name": "facts.txt",
            "content": "Known facts.",
            "reference": "knowledge://item-1",
        }
    ]
    assert result["output"]["ai"]["modules"][0]["id"] == "model-1"
    assert result["output"]["ai"]["status"] == "missing_api_key"


def test_runtime_executes_ai_agent_with_memory_file_module():
    graph = {
        "nodes": [
            {"id": "start", "type": "manual.trigger", "config": {}},
            {
                "id": "agent",
                "type": "ai.agent",
                "config": {
                    "modules": [
                        {
                            "id": "memory-1",
                            "type": "ai.memory.file",
                            "port": "memory",
                            "config": {
                                "name": "memory.txt",
                                "content": "The user prefers short answers.",
                            },
                        },
                    ],
                },
            },
            {"id": "reply", "type": "output.reply", "config": {}},
        ],
        "edges": [
            {"source": "start", "target": "agent"},
            {"source": "agent", "target": "reply"},
        ],
        "settings": {"max_steps": 10},
    }

    result = WorkflowEngine().execute(graph, {"question": "How should you answer?"})

    assert result["status"] == "success"
    assert result["output"]["ai"]["memory"]["files"] == [
        {
            "name": "memory.txt",
            "content": "The user prefers short answers.",
        }
    ]
    assert "The user prefers short answers." in result["output"]["ai"]["prompt"]
