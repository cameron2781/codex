from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "churning.sqlite3"
MIGRATIONS_DIR = BASE_DIR / "migrations"


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def run_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migration (
            filename TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    applied = {
        row["filename"]
        for row in conn.execute("SELECT filename FROM schema_migration").fetchall()
    }
    migration_files: Iterable[Path] = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for file in migration_files:
        if file.name in applied:
            continue
        conn.executescript(file.read_text())
        conn.execute("INSERT INTO schema_migration(filename) VALUES (?)", (file.name,))
    conn.commit()
