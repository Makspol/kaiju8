from datetime import datetime, timezone
from pathlib import Path
import re
from sqlite3 import Connection


MIGRATIONS_DIR = Path(__file__).parent / "migrations"
ADD_COLUMN_PATTERN = re.compile(
    r"^\s*ALTER\s+TABLE\s+(?P<table>[a-zA-Z_][\w]*)\s+"
    r"ADD\s+COLUMN\s+(?P<column>[a-zA-Z_][\w]*)\s+"
    r"(?P<definition>.+?)\s*$",
    re.IGNORECASE | re.DOTALL,
)


def run_migrations(connection: Connection) -> None:
    _ensure_migrations_table(connection)

    applied_migrations = _list_applied_migrations(connection)

    for migration_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        migration_name = migration_path.name

        if migration_name in applied_migrations:
            continue

        _apply_migration(connection, migration_path)
        connection.execute(
            """
            INSERT INTO schema_migrations (name, applied_at)
            VALUES (?, ?)
            """,
            (
                migration_name,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def _ensure_migrations_table(connection: Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def _list_applied_migrations(connection: Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM schema_migrations").fetchall()

    return {row["name"] for row in rows}


def _apply_migration(connection: Connection, migration_path: Path) -> None:
    for statement in _split_statements(migration_path.read_text(encoding="utf-8")):
        add_column = _parse_add_column(statement)

        if add_column and _column_exists(
            connection,
            table=add_column["table"],
            column=add_column["column"],
        ):
            _ensure_column_compatible(
                connection,
                table=add_column["table"],
                column=add_column["column"],
                definition=add_column["definition"],
            )
            continue

        connection.execute(statement)


def _split_statements(script: str) -> list[str]:
    return [
        statement.strip()
        for statement in script.split(";")
        if statement.strip()
    ]


def _parse_add_column(statement: str) -> dict | None:
    match = ADD_COLUMN_PATTERN.match(statement)

    if not match:
        return None

    return match.groupdict()


def _column_exists(connection: Connection, table: str, column: str) -> bool:
    return _get_column(connection, table, column) is not None


def _get_column(connection: Connection, table: str, column: str):
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()

    for row in rows:
        if row["name"].lower() == column.lower():
            return row

    return None


def _ensure_column_compatible(
    connection: Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    existing_column = _get_column(connection, table, column)
    expected_type = definition.split()[0].upper()
    existing_type = str(existing_column["type"] or "").upper()

    if existing_type and existing_type != expected_type:
        raise ValueError(
            f"Column {table}.{column} already exists with type "
            f"{existing_type}, expected {expected_type}."
        )
