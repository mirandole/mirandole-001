import sqlite3
from pathlib import Path

from mirandole.storage import initialize_storage


def test_initialize_storage_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"

    initialize_storage(database_path)
    initialize_storage(database_path)

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'schema_version'"
        ).fetchone()

    assert row == ("1",)
