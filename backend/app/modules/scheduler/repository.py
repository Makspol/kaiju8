import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db.connection import get_connection


ACTIVE = "active"
INACTIVE = "inactive"


def list_schedules(owner_user_id: str | None = None) -> list[dict]:
    with get_connection() as connection:
        if owner_user_id is None:
            rows = connection.execute(
                """
                SELECT * FROM workflow_schedules
                ORDER BY next_run_at ASC, updated_at DESC
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM workflow_schedules
                WHERE owner_user_id = ?
                ORDER BY next_run_at ASC, updated_at DESC
                """,
                (owner_user_id,),
            ).fetchall()

    return [_row_to_schedule(row) for row in rows]


def get_schedule(schedule_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM workflow_schedules WHERE id = ?",
            (schedule_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_schedule(row)


def get_schedule_by_key(workflow_id: str, trigger_node_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM workflow_schedules
            WHERE workflow_id = ? AND trigger_node_id = ?
            """,
            (workflow_id, trigger_node_id),
        ).fetchone()

    if row is None:
        return None

    return _row_to_schedule(row)


def upsert_schedule(
    workflow_id: str,
    owner_user_id: str,
    trigger_node_id: str,
    mode: str,
    schedule: dict,
    next_run_at: datetime,
) -> dict:
    existing = get_schedule_by_key(workflow_id, trigger_node_id)
    now = _now()
    schedule_json = json.dumps(schedule, sort_keys=True)

    if existing is None:
        schedule_id = str(uuid4())

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO workflow_schedules (
                    id,
                    workflow_id,
                    owner_user_id,
                    trigger_node_id,
                    status,
                    mode,
                    schedule_json,
                    next_run_at,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    schedule_id,
                    workflow_id,
                    owner_user_id,
                    trigger_node_id,
                    ACTIVE,
                    mode,
                    schedule_json,
                    _format_datetime(next_run_at),
                    now,
                    now,
                ),
            )

        return get_schedule(schedule_id)

    next_run_value = existing["next_run_at"]

    if (
        existing["schedule_json"] != schedule_json
        or existing["mode"] != mode
        or existing["status"] != ACTIVE
    ):
        next_run_value = _format_datetime(next_run_at)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE workflow_schedules
            SET owner_user_id = ?,
                status = ?,
                mode = ?,
                schedule_json = ?,
                next_run_at = ?,
                last_error = NULL,
                locked_until = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (
                owner_user_id,
                ACTIVE,
                mode,
                schedule_json,
                next_run_value,
                now,
                existing["id"],
            ),
        )

    return get_schedule(existing["id"])


def deactivate_missing(workflow_id: str, active_trigger_node_ids: set[str]) -> int:
    now = _now()

    with get_connection() as connection:
        if active_trigger_node_ids:
            placeholders = ", ".join("?" for _ in active_trigger_node_ids)
            cursor = connection.execute(
                f"""
                UPDATE workflow_schedules
                SET status = ?, next_run_at = NULL, locked_until = NULL, updated_at = ?
                WHERE workflow_id = ?
                  AND trigger_node_id NOT IN ({placeholders})
                """,
                (INACTIVE, now, workflow_id, *active_trigger_node_ids),
            )
        else:
            cursor = connection.execute(
                """
                UPDATE workflow_schedules
                SET status = ?, next_run_at = NULL, locked_until = NULL, updated_at = ?
                WHERE workflow_id = ?
                """,
                (INACTIVE, now, workflow_id),
            )

    return cursor.rowcount


def claim_due_schedules(
    now: datetime,
    lock_until: datetime,
    limit: int = 20,
    owner_user_id: str | None = None,
) -> list[dict]:
    now_text = _format_datetime(now)
    lock_until_text = _format_datetime(lock_until)

    with get_connection() as connection:
        if owner_user_id is None:
            rows = connection.execute(
                """
                SELECT * FROM workflow_schedules
                WHERE status = ?
                  AND next_run_at IS NOT NULL
                  AND next_run_at <= ?
                  AND (locked_until IS NULL OR locked_until <= ?)
                ORDER BY next_run_at ASC
                LIMIT ?
                """,
                (ACTIVE, now_text, now_text, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM workflow_schedules
                WHERE status = ?
                  AND owner_user_id = ?
                  AND next_run_at IS NOT NULL
                  AND next_run_at <= ?
                  AND (locked_until IS NULL OR locked_until <= ?)
                ORDER BY next_run_at ASC
                LIMIT ?
                """,
                (ACTIVE, owner_user_id, now_text, now_text, limit),
            ).fetchall()

        claimed = []

        for row in rows:
            cursor = connection.execute(
                """
                UPDATE workflow_schedules
                SET locked_until = ?, updated_at = ?
                WHERE id = ?
                  AND status = ?
                  AND next_run_at IS NOT NULL
                  AND next_run_at <= ?
                  AND (locked_until IS NULL OR locked_until <= ?)
                """,
                (
                    lock_until_text,
                    now_text,
                    row["id"],
                    ACTIVE,
                    now_text,
                    now_text,
                ),
            )

            if cursor.rowcount == 1:
                claimed.append(row["id"])

    return [
        schedule
        for schedule_id in claimed
        if (schedule := get_schedule(schedule_id)) is not None
    ]


def mark_completed(
    schedule_id: str,
    last_run_at: datetime,
    next_run_at: datetime,
    execution_id: str | None,
    error: str | None = None,
) -> dict | None:
    now = _now()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE workflow_schedules
            SET last_run_at = ?,
                next_run_at = ?,
                last_execution_id = ?,
                last_error = ?,
                locked_until = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (
                _format_datetime(last_run_at),
                _format_datetime(next_run_at),
                execution_id,
                error,
                now,
                schedule_id,
            ),
        )

    return get_schedule(schedule_id)


def mark_failed(
    schedule_id: str,
    last_run_at: datetime,
    next_run_at: datetime,
    error: str,
) -> dict | None:
    now = _now()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE workflow_schedules
            SET last_run_at = ?,
                next_run_at = ?,
                last_error = ?,
                locked_until = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (
                _format_datetime(last_run_at),
                _format_datetime(next_run_at),
                error,
                now,
                schedule_id,
            ),
        )

    return get_schedule(schedule_id)


def _row_to_schedule(row) -> dict:
    schedule = json.loads(row["schedule_json"])

    return {
        "id": row["id"],
        "workflow_id": row["workflow_id"],
        "owner_user_id": row["owner_user_id"],
        "trigger_node_id": row["trigger_node_id"],
        "status": row["status"],
        "mode": row["mode"],
        "schedule": schedule,
        "schedule_json": row["schedule_json"],
        "next_run_at": row["next_run_at"],
        "last_run_at": row["last_run_at"],
        "last_execution_id": row["last_execution_id"],
        "last_error": row["last_error"],
        "locked_until": row["locked_until"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
