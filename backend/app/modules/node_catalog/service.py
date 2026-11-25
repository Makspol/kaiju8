from app.nodes.ai.module_catalog import list_agent_module_types
from app.runtime.registry import NodeRegistry


def list_node_types() -> list[dict]:
    registry = NodeRegistry()
    return [node.metadata() for node in registry.list()]


def list_ai_agent_module_types(port: str | None = None) -> list[dict]:
    return list_agent_module_types(port=port)
