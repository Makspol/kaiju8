import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db.connection import get_connection


def create_execution(
    workflow_id: str,
    input_json: dict,
    result: dict,
) -> dict:
    execution_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    output = result.get("output", {})

    if result.get("usage") is not None:
        output = {
            **output,
            "_usage": result["usage"],
        }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO executions (
                id,
                workflow_id,
                status,
                input_json,
                output_json,
                error,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                workflow_id,
                result["status"],
                json.dumps(input_json),
                json.dumps(output),
                result.get("error"),
                now,
            ),
        )

        for position, step in enumerate(result.get("steps", [])):
            connection.execute(
                """
                INSERT INTO execution_steps (
                    id,
                    execution_id,
                    position,
                    node_id,
                    node_type,
                    status,
                    input_json,
                    output_json,
                    error,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    execution_id,
                    position,
                    step["node_id"],
                    step["node_type"],
                    step["status"],
                    json.dumps(step.get("input", {})),
                    json.dumps(step.get("output")),
                    step.get("error"),
                    now,
                ),
            )

    return get_execution(execution_id)


def get_execution(execution_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM executions WHERE id = ?",
            (execution_id,),
        ).fetchone()

    if row is None:
        return None

    execution = _row_to_execution(row)
    execution["steps"] = list_execution_steps(execution_id)

    return execution


def list_executions(workflow_id: str, limit: int = 50) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM executions
            WHERE workflow_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (workflow_id, limit),
        ).fetchall()

    return [_row_to_execution(row) for row in rows]


def list_execution_steps(execution_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM execution_steps
            WHERE execution_id = ?
            ORDER BY position ASC
            """,
            (execution_id,),
        ).fetchall()

    return [_row_to_step(row) for row in rows]


def workflow_exists_for_owner(
    workflow_id: str,
    owner_user_id: str | None = None,
) -> bool:
    with get_connection() as connection:
        if owner_user_id is None:
            row = connection.execute(
                "SELECT 1 FROM workflows WHERE id = ?",
                (workflow_id,),
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT 1 FROM workflows
                WHERE id = ? AND owner_user_id = ?
                """,
                (workflow_id, owner_user_id),
            ).fetchone()

    return row is not None


def workflow_belongs_to_owner(workflow_id: str, owner_user_id: str) -> bool:
    return workflow_exists_for_owner(
        workflow_id=workflow_id,
        owner_user_id=owner_user_id,
    )


def _row_to_execution(row) -> dict:
    output = json.loads(row["output_json"])

    return {
        "id": row["id"],
        "workflow_id": row["workflow_id"],
        "status": row["status"],
        "input": json.loads(row["input_json"]),
        "output": output,
        "usage": output.get("_usage") if isinstance(output, dict) else None,
        "error": row["error"],
        "created_at": row["created_at"],
    }


def _row_to_step(row) -> dict:
    return {
        "id": row["id"],
        "execution_id": row["execution_id"],
        "position": row["position"],
        "node_id": row["node_id"],
        "node_type": row["node_type"],
        "status": row["status"],
        "input": json.loads(row["input_json"]),
        "output": json.loads(row["output_json"]) if row["output_json"] else None,
        "error": row["error"],
        "created_at": row["created_at"],
    }
