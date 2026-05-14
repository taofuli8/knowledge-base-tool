import json
from typing import List, Optional, Tuple

from .database import get_connection
from .models import EntryCreate, EntryUpdate


def entry_to_dict(row) -> dict:
    tags = row["tags"] if row["tags"] else "[]"
    try:
        tags = json.loads(tags) if isinstance(tags, str) else tags
    except (json.JSONDecodeError, TypeError):
        tags = []
    return {
        "id": row["id"],
        "title": row["title"] or "",
        "url": row["url"] or "",
        "content_type": row["content_type"],
        "raw_content": row["raw_content"] or "",
        "summary": row["summary"] or "",
        "tags": tags,
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_entry(data: EntryCreate) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        tags = json.dumps(data.tags or [])
        cursor.execute(
            """
            INSERT INTO entries (title, url, content_type, raw_content, summary, tags, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """,
            (data.title or "", data.url or "", data.content_type, data.raw_content or "", data.summary or "", tags),
        )
        conn.commit()
        entry_id = cursor.lastrowid
        entry = get_entry(entry_id)
        return entry
    finally:
        conn.close()


def get_entry(entry_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries WHERE id = ? AND status != 'deleted'", (entry_id,))
    row = cursor.fetchone()
    conn.close()
    return entry_to_dict(row) if row else None


def list_entries(page: int = 1, page_size: int = 20, content_type: Optional[str] = None) -> Tuple[int, List[dict]]:
    conn = get_connection()
    cursor = conn.cursor()

    where = "WHERE status != 'deleted'"
    params: list = []

    if content_type:
        where += " AND content_type = ?"
        params.append(content_type)

    cursor.execute(f"SELECT COUNT(*) FROM entries {where}", params)
    total = cursor.fetchone()[0]

    offset = (page - 1) * page_size
    cursor.execute(
        f"SELECT * FROM entries {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset],
    )
    rows = cursor.fetchall()
    conn.close()
    return total, [entry_to_dict(row) for row in rows]


def update_entry(entry_id: int, data: EntryUpdate) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM entries WHERE id = ? AND status != 'deleted'", (entry_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    title = data.title if data.title is not None else row["title"]
    summary = data.summary if data.summary is not None else row["summary"]
    url = data.url if data.url is not None else row["url"]
    tags = json.dumps(data.tags) if data.tags is not None else row["tags"]

    cursor.execute(
        """
        UPDATE entries SET title = ?, summary = ?, url = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (title, summary, url, tags, entry_id),
    )
    conn.commit()
    entry = get_entry(entry_id)
    conn.close()
    return entry


def delete_entry(entry_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE entries SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status != 'deleted'",
        (entry_id,),
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def search_entries(query: str, page: int = 1, page_size: int = 20, content_type: Optional[str] = None, tags: Optional[List[str]] = None) -> Tuple[int, List[dict]]:
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params: list = []

    if content_type:
        conditions.append("e.content_type = ?")
        params.append(content_type)

    if tags:
        for tag in tags:
            conditions.append("e.tags LIKE ?")
            params.append(f"%{tag}%")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    cursor.execute(
        f"""
        SELECT COUNT(*) FROM entries e
        JOIN entries_fts f ON e.id = f.rowid
        WHERE entries_fts MATCH ? AND {where_clause} AND e.status != 'deleted'
        """,
        [query] + params,
    )
    total = cursor.fetchone()[0]

    offset = (page - 1) * page_size
    cursor.execute(
        f"""
        SELECT e.* FROM entries e
        JOIN entries_fts f ON e.id = f.rowid
        WHERE entries_fts MATCH ? AND {where_clause} AND e.status != 'deleted'
        ORDER BY rank LIMIT ? OFFSET ?
        """,
        [query] + params + [page_size, offset],
    )
    rows = cursor.fetchall()
    conn.close()
    return total, [entry_to_dict(row) for row in rows]


def get_raw_content(entry_id: int) -> Optional[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT raw_content FROM entries WHERE id = ? AND status != 'deleted'", (entry_id,))
    row = cursor.fetchone()
    conn.close()
    return row["raw_content"] if row else None


def get_all_tags() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tags FROM entries WHERE status != 'deleted'")
    rows = cursor.fetchall()
    conn.close()

    tag_counts = {}
    for row in rows:
        try:
            tags = json.loads(row["tags"]) if row["tags"] else []
        except (json.JSONDecodeError, TypeError):
            tags = []
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return [{"tag": tag, "count": count} for tag, count in sorted(tag_counts.items())]


def get_entry_count() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM entries WHERE status != 'deleted'")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT content_type, COUNT(*) FROM entries WHERE status != 'deleted' GROUP BY content_type")
    type_counts = {row["content_type"]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM entries WHERE status = 'pending'")
    pending = cursor.fetchone()[0]

    conn.close()
    return {
        "total": total,
        "url": type_counts.get("url", 0),
        "tutorial": type_counts.get("tutorial", 0),
        "github": type_counts.get("github", 0),
        "pending": pending,
    }
