AGENT_NODE_TYPE = "ai.agent"

AGENT_MODULE_PORT_LAYOUT = {
    "top": ["knowledge"],
    "bottom": ["model", "memory", "tools"],
}

AGENT_MODULE_PORT_DEFINITIONS = [
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


def agent_module_port_definitions() -> list[dict]:
    return [
        dict(port)
        for port in AGENT_MODULE_PORT_DEFINITIONS
    ]


def agent_module_port_definition(port_id: str) -> dict | None:
    for port in AGENT_MODULE_PORT_DEFINITIONS:
        if port["id"] == port_id:
            return dict(port)

    return None
