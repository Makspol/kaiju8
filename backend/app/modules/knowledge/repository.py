import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db.connection import get_connection


def create_knowledge_item(
    owner_user_id: str,
    name: str,
    content: str,
    content_type: str,
    metadata: dict,
) -> dict:
    item_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO knowledge_items (
                id,
                owner_user_id,
                name,
                content,
                content_type,
                metadata_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                owner_user_id,
                name,
                content,
                content_type,
                json.dumps(metadata),
                now,
                now,
            ),
        )

    return get_knowledge_item(item_id)


def list_knowledge_items(owner_user_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM knowledge_items
            WHERE owner_user_id = ?
            ORDER BY created_at DESC
            """,
            (owner_user_id,),
        ).fetchall()

    return [_row_to_knowledge_item(row) for row in rows]


def get_knowledge_item(item_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM knowledge_items WHERE id = ?",
            (item_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_knowledge_item(row)


def _row_to_knowledge_item(row) -> dict:
    item_id = row["id"]

    return {
        "id": item_id,
        "owner_user_id": row["owner_user_id"],
        "name": row["name"],
        "content": row["content"],
        "content_type": row["content_type"],
        "metadata": json.loads(row["metadata_json"]),
        "reference": f"knowledge://{item_id}",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
