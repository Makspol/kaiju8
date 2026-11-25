from dataclasses import dataclass

from app.nodes.ai.module_ports import (
    AGENT_NODE_TYPE,
    agent_module_port_definition,
)


@dataclass(frozen=True)
class AgentModuleType:
    type: str
    port: str
    label: str
    description: str
    config_schema: dict

    def metadata(self) -> dict:
        port_definition = agent_module_port_definition(self.port)

        return {
            "type": self.type,
            "category": "ai_agent_module",
            "port": self.port,
            "label": self.label,
            "description": self.description,
            "ports": {"input": False, "output": False},
            "attachable_to": {
                "node_type": AGENT_NODE_TYPE,
                "port": self.port,
                "position": port_definition["position"] if port_definition else None,
            },
            "config_schema": self.config_schema,
        }


class ClaudeModelModule(AgentModuleType):
    def __init__(self):
        super().__init__(
            type="ai.model.claude",
            port="model",
            label="Claude Model",
            description="Connects a Claude model to an AI Agent.",
            config_schema=_model_config_schema(provider="claude"),
        )


class GeminiModelModule(AgentModuleType):
    def __init__(self):
        super().__init__(
            type="ai.model.gemini",
            port="model",
            label="Gemini Model",
            description="Connects a Gemini model to an AI Agent.",
            config_schema=_model_config_schema(provider="gemini"),
        )


class BasicMemoryModule(AgentModuleType):
    def __init__(self):
        super().__init__(
            type="ai.memory.basic",
            port="memory",
            label="Basic Memory",
            description="Stores conversation history used by the AI Agent.",
            config_schema={
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": True},
                    "history": {"type": "array", "default": []},
                },
            },
        )


class MemoryFileModule(AgentModuleType):
    def __init__(self):
        super().__init__(
            type="ai.memory.file",
            port="memory",
            label="Memory File",
            description="Adds file-based conversation memory for an AI Agent.",
            config_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                    "content_type": {"type": "string"},
                    "reference": {"type": "string"},
                },
            },
        )


class HttpRequestToolModule(AgentModuleType):
    def __init__(self):
        super().__init__(
            type="ai.tool.http_request",
            port="tools",
            label="HTTP Request Tool",
            description="Allows an AI Agent to call an HTTP endpoint.",
            config_schema=_http_tool_config_schema(),
        )


class ExternalApiToolModule(AgentModuleType):
    def __init__(self):
        super().__init__(
            type="ai.tool.external_api",
            port="tools",
            label="External API",
            description="Allows an AI Agent to call an external API endpoint.",
            config_schema=_http_tool_config_schema(),
        )


class WebSearchToolModule(AgentModuleType):
    def __init__(self):
        super().__init__(
            type="ai.tool.web_search",
            port="tools",
            label="Internet Search",
            description="Allows an AI Agent to search the internet through a configured search provider.",
            config_schema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "enum": ["brave", "tavily", "custom"],
                        "default": "brave",
                    },
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5},
                    "credential_id": {"type": "string"},
                    "endpoint": {"type": "string"},
                    "query_param": {"type": "string", "default": "q"},
                    "max_results_param": {"type": "string", "default": "count"},
                    "api_key_header": {"type": "string"},
                    "live": {"type": "boolean", "default": False},
                },
            },
        )


class KnowledgeFileModule(AgentModuleType):
    def __init__(self):
        super().__init__(
            type="ai.knowledge.file",
            port="knowledge",
            label="Knowledge File",
            description="Adds file-based facts for an AI Agent to use.",
            config_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                    "content_type": {"type": "string"},
                    "reference": {"type": "string"},
                },
            },
        )


def _model_config_schema(provider: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "provider": {
                "type": "string",
                "const": provider,
                "default": provider,
            },
            "credential_id": {"type": "string"},
            "model_name": {"type": "string"},
            "budget": {"type": "number"},
            "max_llm_calls": {"type": "integer"},
            "max_tokens": {"type": "integer"},
        },
        "node_limits": {
            "budget": {
                "label": "Budget",
                "description": "Maximum estimated AI cost for this model module in one run.",
            },
            "max_llm_calls": {
                "label": "Max calls",
                "description": "Maximum model calls this model module can make in one run.",
            },
            "max_tokens": {
                "label": "Max tokens",
                "description": "Maximum input plus output tokens for this model module in one run.",
            },
        },
    }


def _http_tool_config_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "method": {"type": "string", "default": "GET"},
            "url": {"type": "string"},
            "headers": {"type": "object"},
            "body": {},
            "credential_id": {"type": "string"},
            "api_key_header": {"type": "string"},
            "live": {"type": "boolean", "default": False},
        },
    }
