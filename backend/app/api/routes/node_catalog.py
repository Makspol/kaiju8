from fastapi import APIRouter

from app.modules.node_catalog.service import (
    list_ai_agent_module_types,
    list_node_types,
)


router = APIRouter()


@router.get("")
def get_node_types():
    return list_node_types()


@router.get("/ai-agent/modules")
def get_ai_agent_module_types(port: str | None = None):
    return list_ai_agent_module_types(port=port)
