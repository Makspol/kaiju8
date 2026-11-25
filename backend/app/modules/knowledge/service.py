from app.modules.knowledge import repository
from app.modules.users.service import get_user


def create_knowledge_item(
    owner_user_id: str,
    name: str,
    content: str,
    content_type: str = "text/plain",
    metadata: dict | None = None,
) -> dict | None:
    if get_user(owner_user_id) is None:
        return None

    clean_name = name.strip()
    clean_content = content.strip()
    clean_content_type = content_type.strip() if content_type else "text/plain"

    if not clean_name or not clean_content:
        return None

    return repository.create_knowledge_item(
        owner_user_id=owner_user_id,
        name=clean_name,
        content=clean_content,
        content_type=clean_content_type,
        metadata=metadata or {},
    )


def list_knowledge_items(owner_user_id: str) -> list[dict]:
    return repository.list_knowledge_items(owner_user_id=owner_user_id)


def get_knowledge_item(
    item_id: str,
    owner_user_id: str | None = None,
) -> dict | None:
    item = repository.get_knowledge_item(item_id)

    if item is None:
        return None

    if owner_user_id is None:
        return item

    if item["owner_user_id"] != owner_user_id:
        return None

    return item
