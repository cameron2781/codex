from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MIGRATIONS_DIR = BASE_DIR / "migrations"


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    existing = {
        row["name"]
        for row in conn.execute("SELECT name FROM schema_migrations").fetchall()
    }
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for migration in migration_files:
        if migration.name in existing:
            continue
        conn.executescript(migration.read_text())
        conn.execute(
            "INSERT INTO schema_migrations(name) VALUES (?)",
            (migration.name,),
        )
    conn.commit()
