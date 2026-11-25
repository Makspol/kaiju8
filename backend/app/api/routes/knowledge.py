from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import get_current_user
from app.modules.knowledge.service import (
    create_knowledge_item,
    get_knowledge_item,
    list_knowledge_items,
)
from app.schemas.knowledge import CreateKnowledgeItemRequest


router = APIRouter()


@router.post("")
def create_knowledge_item_route(
    payload: CreateKnowledgeItemRequest,
    current_user: dict = Depends(get_current_user),
):
    item = create_knowledge_item(
        owner_user_id=current_user["id"],
        name=payload.name,
        content=payload.content,
        content_type=payload.content_type,
        metadata=payload.metadata,
    )

    if item is None:
        raise HTTPException(status_code=400, detail="Invalid knowledge item")

    return item


@router.get("")
def list_knowledge_items_route(
    current_user: dict = Depends(get_current_user),
):
    return list_knowledge_items(owner_user_id=current_user["id"])


@router.get("/{item_id}")
def get_knowledge_item_route(
    item_id: str,
    current_user: dict = Depends(get_current_user),
):
    item = get_knowledge_item(
        item_id=item_id,
        owner_user_id=current_user["id"],
    )

    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    return item
