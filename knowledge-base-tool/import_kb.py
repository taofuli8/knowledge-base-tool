import json
import sys
import os
import httpx

DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge.db")
os.environ.setdefault("KNOWLEDGE_DB_PATH", DB_PATH)

from app.database import init_db
from app.models import EntryCreate, EntryUpdate
from app import crud


def import_knowledge(json_path, api_url=None):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    print(f"Found {len(items)} items in export")

    if api_url:
        import_via_api(api_url, items)
    else:
        import_via_db(items)


def import_via_db(items):
    init_db()
    success = 0
    failed = 0

    for item in items:
        try:
            url = item.get("url", "")
            title = item.get("title", "")
            raw_content = item.get("raw_content", "") or ""
            summary = item.get("summary_zh", "") or ""
            tags = item.get("tags") or []

            entry = crud.create_entry(EntryCreate(
                url=url,
                content_type="github",
                title=title,
                raw_content=raw_content[:50000],
            ))

            if entry:
                if tags or summary:
                    crud.update_entry(
                        entry["id"],
                        EntryUpdate(
                            summary=summary[:2000] if summary else None,
                            tags=tags if tags else None,
                        ),
                    )

            success += 1
            if success % 50 == 0:
                print(f"Imported {success}/{len(items)}...")
        except Exception as e:
            failed += 1
            print(f"Failed to import {item.get('title', 'unknown')}: {e}")

    print(f"Done! Success: {success}, Failed: {failed}")


def import_via_api(api_url, items):
    success = 0
    failed = 0

    for item in items:
        try:
            resp = httpx.post(f"{api_url}/entries", json={
                "url": item.get("url", ""),
                "content_type": "github",
                "title": item.get("title", ""),
                "raw_content": item.get("raw_content", "")[:50000],
            })
            if resp.status_code != 200:
                raise Exception(f"API error: {resp.text}")

            entry = resp.json()
            tags = item.get("tags", [])
            summary = item.get("summary_zh", "")[:2000]
            if tags or summary:
                httpx.put(f"{api_url}/entries/{entry['id']}", json={
                    "summary": summary,
                    "tags": tags,
                })

            success += 1
            if success % 50 == 0:
                print(f"Imported {success}/{len(items)}...")
        except Exception as e:
            failed += 1
            print(f"Failed to import {item.get('title', 'unknown')}: {e}")

    print(f"Done! Success: {success}, Failed: {failed}")


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "github-kb-2026-05-14.json"
    api_url = sys.argv[2] if len(sys.argv) > 2 else None
    import_knowledge(json_path, api_url)
