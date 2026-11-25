from datetime import datetime, timezone
from uuid import uuid4

from app.db.connection import get_connection


def create_user(
    email: str,
    name: str,
    password_hash: str | None = None,
) -> dict:
    user_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (id, email, name, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, email, name, password_hash, now),
        )

    return get_user(user_id)


def get_user(user_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_user(row)


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_user(row)


def get_user_with_password_by_email(email: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if row is None:
        return None

    user = _row_to_user(row)
    user["password_hash"] = row["password_hash"]

    return user


def list_users() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM users ORDER BY created_at DESC"
        ).fetchall()

    return [_row_to_user(row) for row in rows]


def update_user_password_hash(user_id: str, password_hash: str) -> dict | None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (password_hash, user_id),
        )

    return get_user(user_id)


def _row_to_user(row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "created_at": row["created_at"],
    }
