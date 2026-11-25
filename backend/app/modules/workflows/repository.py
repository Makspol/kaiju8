import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db.connection import get_connection


DEFAULT_GRAPH = {
    "nodes": [],
    "edges": [],
    "settings": {"max_steps": 20},
}


def create_workflow(
    name: str,
    graph: dict | None = None,
    owner_user_id: str | None = None,
) -> dict:
    workflow_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    graph = graph or DEFAULT_GRAPH

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO workflows (
                id,
                owner_user_id,
                name,
                graph_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (workflow_id, owner_user_id, name, json.dumps(graph), now, now),
        )

    return get_workflow(workflow_id)


def list_workflows(owner_user_id: str | None = None) -> list[dict]:
    with get_connection() as connection:
        if owner_user_id is None:
            rows = connection.execute(
                "SELECT * FROM workflows ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM workflows
                WHERE owner_user_id = ?
                ORDER BY created_at DESC
                """,
                (owner_user_id,),
            ).fetchall()

    return [_row_to_workflow(row) for row in rows]


def get_workflow(workflow_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM workflows WHERE id = ?",
            (workflow_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_workflow(row)


def update_workflow(workflow_id: str, payload: dict) -> dict | None:
    workflow = get_workflow(workflow_id)

    if workflow is None:
        return None

    name = payload.get("name", workflow["name"])
    graph = payload.get("graph", workflow["graph"])
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE workflows
            SET name = ?, graph_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, json.dumps(graph), now, workflow_id),
        )

    return get_workflow(workflow_id)


def delete_workflow(
    workflow_id: str,
    owner_user_id: str | None = None,
) -> bool:
    with get_connection() as connection:
        if owner_user_id is None:
            workflow = connection.execute(
                "SELECT id FROM workflows WHERE id = ?",
                (workflow_id,),
            ).fetchone()
        else:
            workflow = connection.execute(
                """
                SELECT id FROM workflows
                WHERE id = ? AND owner_user_id = ?
                """,
                (workflow_id, owner_user_id),
            ).fetchone()

        if workflow is None:
            return False

        connection.execute(
            """
            DELETE FROM execution_steps
            WHERE execution_id IN (
                SELECT id FROM executions
                WHERE workflow_id = ?
            )
            """,
            (workflow_id,),
        )
        connection.execute(
            "DELETE FROM executions WHERE workflow_id = ?",
            (workflow_id,),
        )
        cursor = connection.execute(
            "DELETE FROM workflows WHERE id = ?",
            (workflow_id,),
        )

    return cursor.rowcount > 0


def _row_to_workflow(row) -> dict:
    return {
        "id": row["id"],
        "owner_user_id": row["owner_user_id"],
        "name": row["name"],
        "graph": json.loads(row["graph_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
