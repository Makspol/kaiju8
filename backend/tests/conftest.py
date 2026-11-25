import os
import tempfile

import pytest

from app.db.connection import init_db


file_descriptor, collection_database_path = tempfile.mkstemp()
os.close(file_descriptor)
os.environ["KAIJU8_DB_PATH"] = collection_database_path


@pytest.fixture(autouse=True)
def isolated_database():
    file_descriptor, database_path = tempfile.mkstemp()
    os.close(file_descriptor)

    previous_database_path = os.environ.get("KAIJU8_DB_PATH")
    os.environ["KAIJU8_DB_PATH"] = database_path

    init_db()

    yield

    if previous_database_path is None:
        os.environ.pop("KAIJU8_DB_PATH", None)
    else:
        os.environ["KAIJU8_DB_PATH"] = previous_database_path

    try:
        os.remove(database_path)
    except FileNotFoundError:
        pass
