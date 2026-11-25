import pytest
from fastapi import HTTPException

from app.api.routes.knowledge import (
    create_knowledge_item_route,
    get_knowledge_item_route,
    list_knowledge_items_route,
)
from app.modules.knowledge.service import (
    create_knowledge_item,
    get_knowledge_item,
    list_knowledge_items,
)
from app.modules.users.service import create_user
from app.schemas.knowledge import CreateKnowledgeItemRequest


def test_create_knowledge_item_returns_reference():
    user = create_user(email="owner@example.com", name="Owner")

    item = create_knowledge_item(
        owner_user_id=user["id"],
        name="Facts.txt",
        content="Project facts.",
        content_type="text/plain",
        metadata={"source": "manual"},
    )

    assert item["owner_user_id"] == user["id"]
    assert item["name"] == "Facts.txt"
    assert item["content"] == "Project facts."
    assert item["content_type"] == "text/plain"
    assert item["metadata"] == {"source": "manual"}
    assert item["reference"] == f"knowledge://{item['id']}"


def test_knowledge_items_are_scoped_to_owner():
    owner = create_user(email="owner@example.com", name="Owner")
    other_user = create_user(email="other@example.com", name="Other")

    item = create_knowledge_item(
        owner_user_id=owner["id"],
        name="Private facts",
        content="Only owner can see this.",
    )

    assert list_knowledge_items(owner_user_id=owner["id"])[0]["id"] == item["id"]
    assert list_knowledge_items(owner_user_id=other_user["id"]) == []
    assert get_knowledge_item(item["id"], owner_user_id=owner["id"]) is not None
    assert get_knowledge_item(item["id"], owner_user_id=other_user["id"]) is None


def test_knowledge_routes_use_current_user_scope():
    owner = create_user(email="owner@example.com", name="Owner")
    other_user = create_user(email="other@example.com", name="Other")

    item = create_knowledge_item_route(
        payload=CreateKnowledgeItemRequest(
            name="Route facts",
            content="Facts from route.",
            metadata={"filename": "facts.txt"},
        ),
        current_user=owner,
    )

    assert list_knowledge_items_route(current_user=owner)[0]["id"] == item["id"]
    assert get_knowledge_item_route(
        item_id=item["id"],
        current_user=owner,
    )["reference"] == item["reference"]

    with pytest.raises(HTTPException):
        get_knowledge_item_route(
            item_id=item["id"],
            current_user=other_user,
        )


def test_create_knowledge_item_rejects_empty_content():
    user = create_user(email="owner@example.com", name="Owner")

    item = create_knowledge_item(
        owner_user_id=user["id"],
        name="Empty",
        content=" ",
    )

    assert item is None
