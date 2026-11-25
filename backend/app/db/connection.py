import os
import sqlite3
from pathlib import Path


def get_database_path() -> str:
    return os.getenv("KAIJU8_DB_PATH", "kaiju8.db")


def get_connection():
    db_path = get_database_path()

    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        from app.db.migrator import run_migrations

        run_migrations(connection)
