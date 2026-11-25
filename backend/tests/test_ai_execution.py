from time import sleep

from app.modules.credentials.service import create_credential
from app.modules.knowledge.service import create_knowledge_item
from app.modules.users.service import create_user
from app.nodes.ai.agent_node import AiAgentNode
from app.nodes.ai.execution.providers import AiProviderResponse
from app.nodes.ai.execution.service import AiExecutionService
from app.nodes.ai.execution.tools import run_tools
from app.runtime.limits import ExecutionLimitExceeded
from app.runtime.types import ExecutionContext


class FakeProvider:
    def generate(
        self,
        prompt: str,
        api_key: str,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ):
        return AiProviderResponse(
            text=f"answer from {model or 'default'}",
            raw={
                "prompt": prompt,
                "api_key": api_key,
                "model": model,
                "timeout_seconds": timeout_seconds,
            },
        )


class FakeProviderRegistry:
    def get(self, provider: str):
        if provider == "gemini":
            return FakeProvider()

        return None


class SlowExecutionService:
    def execute_agent(self, **kwargs):
        sleep(0.01)
        return {
            "status": "success",
            "error": None,
            "response": "too slow",
            "prompt": kwargs["prompt"],
            "tool_results": [],
            "knowledge": [],
            "usage": kwargs["context"].usage.as_dict(),
        }


def test_ai_execution_returns_missing_api_key_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={"provider": "gemini"},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=ExecutionContext(initial_input={}),
    )

    assert result["status"] == "missing_api_key"
    assert "GEMINI_API_KEY" in result["error"]
    assert result["response"] is None


def test_ai_execution_calls_provider_with_env_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={"provider": "gemini", "model_name": "gemini-test"},
        memory={"enabled": True, "history": [{"role": "user", "content": "Hi"}]},
        tools=[],
        knowledge=[{"name": "facts.txt", "content": "Known facts."}],
        input_data={"question": "Hello?"},
        context=ExecutionContext(initial_input={}),
    )

    assert result["status"] == "success"
    assert result["response"] == "answer from gemini-test"
    assert result["raw_response"]["api_key"] == "test-key"
    assert result["raw_response"]["timeout_seconds"] is None
    assert "Known facts." in result["prompt"]
    assert "Hello?" in result["prompt"]
    assert result["usage"]["llm_calls"] == 1
    assert result["usage"]["tokens_used"] > 0


def test_ai_execution_passes_agent_timeout_to_provider(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={"provider": "gemini"},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=ExecutionContext(initial_input={}),
        timeout_seconds=5,
    )

    assert result["status"] == "success"
    assert result["raw_response"]["timeout_seconds"] <= 5


def test_ai_agent_node_stops_when_timeout_is_exceeded():
    node = AiAgentNode(execution_service=SlowExecutionService())

    try:
        node.execute(
            config={
                "prompt": "Answer",
                "model": {"provider": "gemini"},
                "timeout_seconds": 0.001,
            },
            input_data={},
            context=ExecutionContext(initial_input={}),
        )
    except ExecutionLimitExceeded as error:
        assert error.code == "ai_node_timeout_exceeded"
    else:
        raise AssertionError("Expected AI Agent node timeout to be enforced.")


def test_ai_execution_resolves_owned_model_credential(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    user = create_user(email="owner@example.com", name="Owner")
    credential = create_credential(
        owner_user_id=user["id"],
        name="Gemini",
        provider="gemini",
        secret_value="stored-key",
    )
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={
            "provider": "gemini",
            "credential_id": credential["id"],
        },
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=ExecutionContext(
            initial_input={},
            owner_user_id=user["id"],
        ),
    )

    assert result["status"] == "success"
    assert result["raw_response"]["api_key"] == "stored-key"


def test_agent_tools_resolve_http_request_templates_in_dry_run():
    results = run_tools(
        [
            {
                "type": "http_request",
                "config": {
                    "method": "POST",
                    "url": "https://api.example.com/customers/{{ customer.id }}",
                    "headers": {"Authorization": "Bearer {{ token }}"},
                    "body": {"email": "{{ customer.email }}"},
                },
            }
        ],
        input_data={
            "token": "secret-token",
            "customer": {
                "id": "c-123",
                "email": "jane@example.com",
            },
        },
    )

    assert results == [
        {
            "type": "http_request",
            "status": "dry_run",
            "request": {
                "method": "POST",
                "url": "https://api.example.com/customers/c-123",
                "headers": {"Authorization": "***"},
                "body": {"email": "jane@example.com"},
            },
        }
    ]


def test_agent_tools_can_use_owned_credential_in_http_request_dry_run():
    user = create_user(email="owner@example.com", name="Owner")
    credential = create_credential(
        owner_user_id=user["id"],
        name="CRM token",
        provider="custom",
        secret_value="crm-secret",
    )

    results = run_tools(
        [
            {
                "type": "http_request",
                "config": {
                    "method": "GET",
                    "url": "https://api.example.com/customers",
                    "credential_id": credential["id"],
                    "api_key_header": "X-Api-Key",
                },
            }
        ],
        owner_user_id=user["id"],
    )

    assert results[0]["status"] == "dry_run"
    assert results[0]["request"]["headers"]["X-Api-Key"] == "***"


def test_agent_tools_support_web_search_dry_run():
    results = run_tools(
        [
            {
                "type": "web_search",
                "config": {
                    "provider": "brave",
                    "query": "{{ question }}",
                    "max_results": 3,
                },
            }
        ],
        input_data={"question": "latest AI workflow automation"},
    )

    assert results == [
        {
            "type": "web_search",
            "status": "dry_run",
            "request": {
                "provider": "brave",
                "query": "latest AI workflow automation",
                "max_results": 3,
            },
            "results": [],
        }
    ]


def test_ai_execution_resolves_owned_knowledge_reference(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    user = create_user(email="owner@example.com", name="Owner")
    item = create_knowledge_item(
        owner_user_id=user["id"],
        name="facts.txt",
        content="Stored facts.",
    )
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Use knowledge",
        model={"provider": "gemini"},
        memory={"enabled": False},
        tools=[],
        knowledge=[{"reference": item["reference"]}],
        input_data={},
        context=ExecutionContext(
            initial_input={},
            owner_user_id=user["id"],
        ),
    )

    assert result["status"] == "success"
    assert result["knowledge"][0]["content"] == "Stored facts."
    assert result["knowledge"][0]["reference"] == item["reference"]


def test_ai_execution_stops_when_llm_call_limit_is_exceeded(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={"provider": "gemini"},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=ExecutionContext(
            initial_input={},
            max_llm_calls=0,
        ),
    )

    assert result["status"] == "max_llm_calls_exceeded"
    assert result["response"] is None
    assert result["usage"]["llm_calls"] == 0


def test_ai_execution_stops_when_provider_llm_call_limit_is_exceeded(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={"provider": "gemini"},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=ExecutionContext(
            initial_input={},
            ai_limits={"gemini": {"max_llm_calls": 0}},
        ),
    )

    assert result["status"] == "gemini_max_llm_calls_exceeded"
    assert result["response"] is None
    assert result["usage"]["by_provider"]["gemini"]["llm_calls"] == 0


def test_ai_execution_stops_when_node_llm_call_limit_is_exceeded(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={"provider": "gemini", "max_llm_calls": 0},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=ExecutionContext(initial_input={}),
    )

    assert result["status"] == "ai_node_max_llm_calls_exceeded"
    assert result["response"] is None
    assert result["usage"]["llm_calls"] == 0


def test_ai_execution_stops_when_token_limit_is_exceeded(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="This prompt is too large for one token",
        model={"provider": "gemini"},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={},
        context=ExecutionContext(
            initial_input={},
            max_tokens=1,
        ),
    )

    assert result["status"] == "max_tokens_exceeded"
    assert result["response"] is None


def test_ai_execution_stops_when_node_token_limit_is_exceeded(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="This prompt is too large for one token",
        model={"provider": "gemini", "max_tokens": 1},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={},
        context=ExecutionContext(initial_input={}),
    )

    assert result["status"] == "ai_node_max_tokens_exceeded"
    assert result["response"] is None


def test_ai_execution_tracks_provider_usage_separately(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())
    context = ExecutionContext(
        initial_input={},
        ai_limits={"claude": {"max_llm_calls": 0}, "gemini": {"max_llm_calls": 1}},
    )

    result = service.execute_agent(
        prompt="Answer",
        model={"provider": "gemini"},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=context,
    )

    assert result["status"] == "success"
    assert result["usage"]["by_provider"]["gemini"]["llm_calls"] == 1
    assert "claude" not in result["usage"]["by_provider"]


def test_ai_execution_uses_default_provider_call_limit(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())
    context = ExecutionContext(initial_input={})

    result = None
    for _ in range(21):
        result = service.execute_agent(
            prompt="Answer",
            model={"provider": "gemini"},
            memory={"enabled": True, "history": []},
            tools=[],
            knowledge=[],
            input_data={"question": "Hello?"},
            context=context,
        )

    assert result is not None
    assert result["status"] == "gemini_max_llm_calls_exceeded"
    assert result["usage"]["by_provider"]["gemini"]["llm_calls"] == 20


def test_ai_execution_stops_when_budget_is_exceeded(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={"provider": "gemini"},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=ExecutionContext(
            initial_input={},
            budget=0,
        ),
    )

    assert result["status"] == "budget_exceeded"
    assert result["response"] is None
    assert result["usage"]["budget_used"] > 0


def test_ai_execution_stops_when_provider_budget_is_exceeded(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={"provider": "gemini"},
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=ExecutionContext(
            initial_input={},
            ai_limits={"gemini": {"budget": 0}},
        ),
    )

    assert result["status"] == "gemini_budget_exceeded"
    assert result["response"] is None
    assert result["usage"]["by_provider"]["gemini"]["budget_used"] > 0


def test_ai_execution_stops_when_node_budget_is_exceeded(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = AiExecutionService(provider_registry=FakeProviderRegistry())

    result = service.execute_agent(
        prompt="Answer",
        model={
            "provider": "gemini",
            "budget": 0,
        },
        memory={"enabled": True, "history": []},
        tools=[],
        knowledge=[],
        input_data={"question": "Hello?"},
        context=ExecutionContext(initial_input={}),
    )

    assert result["status"] == "ai_node_budget_exceeded"
    assert result["response"] is None
    assert result["usage"]["budget_used"] > 0
