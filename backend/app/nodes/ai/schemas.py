from app.nodes.ai.constants import SUPPORTED_AGENT_MODELS, SUPPORTED_AGENT_TOOLS
from app.nodes.ai.module_ports import (
    AGENT_MODULE_PORT_LAYOUT,
    agent_module_port_definitions,
)


def agent_config_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "output_path": {
                "type": "string",
                "description": "Optional dot path where the agent response should be saved.",
            },
            "timeout_seconds": {
                "type": "number",
                "minimum": 0.001,
                "description": "Optional wall-clock timeout for this AI Agent node.",
            },
            "routing": {
                "type": "object",
                "description": "Optional route selection for agent-as-router workflows.",
                "properties": {
                    "enabled": {"type": "boolean", "default": True},
                    "strategy": {
                        "type": "string",
                        "enum": ["field_match", "ai_response"],
                        "default": "field_match",
                    },
                    "field": {"type": "string"},
                    "routes": {"type": "array", "default": []},
                    "default_route": {"type": "string"},
                },
            },
            "model": {
                "type": "object",
                "default": {"provider": "claude"},
                "properties": {
                    "provider": {
                        "type": "string",
                        "enum": SUPPORTED_AGENT_MODELS,
                        "default": "claude",
                    },
                    "credential_id": {"type": "string"},
                    "model_name": {"type": "string"},
                    "budget": {"type": "number"},
                    "max_llm_calls": {"type": "integer"},
                    "max_tokens": {"type": "integer"},
                },
            },
            "memory": {
                "type": "object",
                "default": {"enabled": True},
                "properties": {
                    "enabled": {"type": "boolean", "default": True},
                    "history": {"type": "array", "default": []},
                },
            },
            "tools": {
                "type": "array",
                "default": [],
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": SUPPORTED_AGENT_TOOLS,
                        },
                        "config": {"type": "object"},
                    },
                },
            },
            "knowledge": {
                "type": "array",
                "default": [],
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "content": {"type": "string"},
                        "content_type": {"type": "string"},
                        "reference": {"type": "string"},
                    },
                },
            },
            "modules": {
                "type": "array",
                "default": [],
                "items": {
                    "type": "object",
                    "required": ["id", "type", "port"],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string"},
                        "port": {"type": "string"},
                        "config": {"type": "object"},
                    },
                },
            },
        },
        "module_storage": {
            "strategy": "node_config_modules",
            "path": "config.modules",
            "description": "Visual AI Agent modules are stored inside the ai.agent node config.",
        },
        "module_port_layout": AGENT_MODULE_PORT_LAYOUT,
        "module_ports": agent_module_port_definitions(),
        "supported_models": SUPPORTED_AGENT_MODELS,
        "supported_tools": SUPPORTED_AGENT_TOOLS,
    }
