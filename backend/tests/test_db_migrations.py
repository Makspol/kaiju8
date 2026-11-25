import sqlite3

from app.db.connection import get_connection, init_db
from app.db.migrator import run_migrations


def test_init_db_applies_migrations_once():
    init_db()
    init_db()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT name FROM schema_migrations
            ORDER BY name ASC
            """
        ).fetchall()

    migration_names = [row["name"] for row in rows]

    assert migration_names == [
        "001_create_workflows.sql",
        "002_create_executions.sql",
        "003_create_users_and_workflow_ownership.sql",
        "004_add_user_password_hash.sql",
        "005_create_knowledge_items.sql",
        "006_create_workflow_schedules.sql",
        "007_create_api_credentials.sql",
    ]


def test_migrations_create_expected_tables():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name ASC
            """
        ).fetchall()

    table_names = {row["name"] for row in rows}

    assert "workflows" in table_names
    assert "executions" in table_names
    assert "execution_steps" in table_names
    assert "users" in table_names
    assert "knowledge_items" in table_names
    assert "workflow_schedules" in table_names
    assert "api_credentials" in table_names
    assert "workspaces" not in table_names
    assert "schema_migrations" in table_names


def test_workflows_table_uses_direct_owner():
    with get_connection() as connection:
        rows = connection.execute("PRAGMA table_info(workflows)").fetchall()

    column_names = {row["name"] for row in rows}

    assert "owner_user_id" in column_names
    assert "workspace_id" not in column_names


def test_migrations_tolerate_existing_matching_columns_from_old_local_db(tmp_path):
    database_path = tmp_path / "old-local.db"
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE schema_migrations (
            name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE workflows (
            id TEXT PRIMARY KEY,
            owner_user_id TEXT,
            name TEXT NOT NULL,
            graph_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            password_hash TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.executemany(
        "INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)",
        [
            ("001_create_workflows.sql", "2026-01-01T00:00:00+00:00"),
            ("002_create_executions.sql", "2026-01-01T00:00:00+00:00"),
            ("003_create_users_workspaces.sql", "2026-01-01T00:00:00+00:00"),
            ("004_add_user_password_hash.sql", "2026-01-01T00:00:00+00:00"),
            ("005_remove_workspaces.sql", "2026-01-01T00:00:00+00:00"),
        ],
    )

    run_migrations(connection)

    workflow_columns = [
        row["name"]
        for row in connection.execute("PRAGMA table_info(workflows)").fetchall()
    ]
    migration_names = {
        row["name"]
        for row in connection.execute("SELECT name FROM schema_migrations").fetchall()
    }
    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    assert workflow_columns.count("owner_user_id") == 1
    assert "003_create_users_and_workflow_ownership.sql" in migration_names
    assert "005_create_knowledge_items.sql" in migration_names
    assert "007_create_api_credentials.sql" in migration_names
    assert "knowledge_items" in tables
    assert "api_credentials" in tables
