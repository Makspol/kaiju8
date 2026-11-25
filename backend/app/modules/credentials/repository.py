from datetime import datetime, timezone
from uuid import uuid4

from app.db.connection import get_connection


def create_credential(
    owner_user_id: str,
    name: str,
    provider: str,
    secret_value: str,
) -> dict:
    credential_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO api_credentials (
                id,
                owner_user_id,
                name,
                provider,
                secret_value,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                credential_id,
                owner_user_id,
                name,
                provider,
                secret_value,
                now,
                now,
            ),
        )

    return get_credential(credential_id)


def list_credentials(owner_user_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM api_credentials
            WHERE owner_user_id = ?
            ORDER BY created_at DESC
            """,
            (owner_user_id,),
        ).fetchall()

    return [_row_to_public_credential(row) for row in rows]


def get_credential(credential_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM api_credentials
            WHERE id = ?
            """,
            (credential_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_public_credential(row)


def get_credential_for_owner(
    credential_id: str,
    owner_user_id: str,
) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM api_credentials
            WHERE id = ? AND owner_user_id = ?
            """,
            (credential_id, owner_user_id),
        ).fetchone()

    if row is None:
        return None

    return _row_to_public_credential(row)


def get_credential_secret(
    credential_id: str,
    owner_user_id: str,
) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, owner_user_id, provider, secret_value
            FROM api_credentials
            WHERE id = ? AND owner_user_id = ?
            """,
            (credential_id, owner_user_id),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "owner_user_id": row["owner_user_id"],
        "provider": row["provider"],
        "secret_value": row["secret_value"],
    }


def update_credential(
    credential_id: str,
    owner_user_id: str,
    payload: dict,
) -> dict | None:
    if not payload:
        return get_credential_for_owner(
            credential_id=credential_id,
            owner_user_id=owner_user_id,
        )

    allowed_fields = {"name", "provider", "secret_value"}
    fields = [
        field
        for field in allowed_fields
        if field in payload
    ]

    if not fields:
        return get_credential_for_owner(
            credential_id=credential_id,
            owner_user_id=owner_user_id,
        )

    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [payload[field] for field in fields]
    values.extend([
        datetime.now(timezone.utc).isoformat(),
        credential_id,
        owner_user_id,
    ])

    with get_connection() as connection:
        connection.execute(
            f"""
            UPDATE api_credentials
            SET {assignments},
                updated_at = ?
            WHERE id = ? AND owner_user_id = ?
            """,
            values,
        )

    return get_credential_for_owner(
        credential_id=credential_id,
        owner_user_id=owner_user_id,
    )


def delete_credential(
    credential_id: str,
    owner_user_id: str,
) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM api_credentials
            WHERE id = ? AND owner_user_id = ?
            """,
            (credential_id, owner_user_id),
        )

    return cursor.rowcount > 0


def _row_to_public_credential(row) -> dict:
    return {
        "id": row["id"],
        "owner_user_id": row["owner_user_id"],
        "name": row["name"],
        "provider": row["provider"],
        "secret_set": bool(row["secret_value"]),
        "secret_hint": _secret_hint(row["secret_value"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _secret_hint(secret_value: str) -> str:
    if len(secret_value) <= 4:
        return "****"

    return f"****{secret_value[-4:]}"
