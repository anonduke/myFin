from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


DEFAULT_DB_NAME = "finance.db"


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def execute_script(conn: sqlite3.Connection, statements: Iterable[str]) -> None:
    for stmt in statements:
        conn.executescript(stmt)


def load_schema() -> str:
    schema_path = Path(__file__).with_name("schema.sql")
    return schema_path.read_text(encoding="ascii")


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema = load_schema()
    with get_connection(db_path) as conn:
        conn.executescript(schema)
