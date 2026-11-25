from app.modules.knowledge.service import get_knowledge_item


def resolve_knowledge_items(
    knowledge: list[dict],
    owner_user_id: str | None,
) -> list[dict]:
    resolved = []

    for item in knowledge:
        reference = item.get("reference")

        if reference and reference.startswith("knowledge://"):
            stored_item = _get_stored_knowledge_item(reference, owner_user_id)

            if stored_item:
                resolved.append({
                    "name": stored_item["name"],
                    "content": stored_item["content"],
                    "content_type": stored_item["content_type"],
                    "reference": stored_item["reference"],
                    "metadata": stored_item["metadata"],
                })
                continue

        resolved.append(item)

    return resolved


def _get_stored_knowledge_item(
    reference: str,
    owner_user_id: str | None,
) -> dict | None:
    item_id = reference.removeprefix("knowledge://")

    if not item_id:
        return None

    return get_knowledge_item(
        item_id=item_id,
        owner_user_id=owner_user_id,
    )
