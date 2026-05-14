import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv("KNOWLEDGE_DB_PATH", str(Path(__file__).parent.parent / "knowledge.db"))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT '',
            url TEXT DEFAULT '',
            content_type TEXT NOT NULL CHECK(content_type IN ('url', 'tutorial', 'github')),
            raw_content TEXT DEFAULT '',
            summary TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processed', 'deleted', 'error')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
            title, summary, url, tags,
            content='entries',
            content_rowid='id'
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(rowid, title, summary, url, tags)
            VALUES (new.id, new.title, new.summary, new.url, new.tags);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, title, summary, url, tags)
            VALUES ('delete', old.id, old.title, old.summary, old.url, old.tags);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, title, summary, url, tags)
            VALUES ('delete', old.id, old.title, old.summary, old.url, old.tags);
            INSERT INTO entries_fts(rowid, title, summary, url, tags)
            VALUES (new.id, new.title, new.summary, new.url, new.tags);
        END
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
