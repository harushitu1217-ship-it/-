from __future__ import annotations

from contextlib import contextmanager
import sqlite3
from pathlib import Path


def connect(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else Path(__file__).resolve().parents[2] / "data" / "mingjing.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def open_connection(db_path: str | None = None):
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def initialize_database(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            content_type TEXT NOT NULL,
            platform TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            tags TEXT NOT NULL,
            keywords TEXT NOT NULL,
            image_suggestions TEXT NOT NULL,
            publish_tip TEXT NOT NULL,
            optional_script TEXT,
            image_assets TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(generated_history)").fetchall()}
    if "image_assets" not in columns:
        conn.execute("ALTER TABLE generated_history ADD COLUMN image_assets TEXT NOT NULL DEFAULT '[]'")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            api_url TEXT NOT NULL,
            api_key TEXT NOT NULL,
            model TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS platform_auth_configs (
            platform TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL,
            redirect_uri TEXT NOT NULL,
            scopes TEXT NOT NULL DEFAULT '[]',
            auth_url_template TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
