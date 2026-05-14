from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from .models import EntryCreate, EntryUpdate, EntryResponse, SearchResponse
from . import crud
from .scraper import fetch_web_content, fetch_github_readme, fetch_github_info

router = APIRouter(prefix="/api", tags=["entries"])


@router.post("/entries", response_model=EntryResponse)
async def create_entry(data: EntryCreate):
    return crud.create_entry(data)


@router.get("/entries")
async def list_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    content_type: Optional[str] = None,
):
    total, items = crud.list_entries(page, page_size, content_type)
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/entries/search")
async def search_entries(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    content_type: Optional[str] = None,
    tags: Optional[str] = None,
):
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    total, items = crud.search_entries(q, page, page_size, content_type, tag_list)
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/entries/{entry_id}", response_model=EntryResponse)
async def get_entry(entry_id: int):
    entry = crud.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.put("/entries/{entry_id}", response_model=EntryResponse)
async def update_entry(entry_id: int, data: EntryUpdate):
    entry = crud.update_entry(entry_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int):
    if not crud.delete_entry(entry_id):
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted successfully"}


@router.get("/entries/{entry_id}/content")
async def get_entry_content(entry_id: int):
    entry = crud.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"content": entry.get("raw_content", ""), "content_type": entry["content_type"]}


@router.post("/entries/{entry_id}/summary")
async def update_entry_summary(entry_id: int, summary: str):
    data = EntryUpdate(summary=summary)
    entry = crud.update_entry(entry_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if len(summary) > 2000:
        entry["summary"] = summary[:2000]
        crud.update_entry(entry_id, EntryUpdate(summary=summary[:2000]))
    return entry


@router.get("/entries/{entry_id}/fetch-content")
async def fetch_content(entry_id: int):
    entry = crud.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry["content_type"] == "url":
        result = await fetch_web_content(entry["url"])
    elif entry["content_type"] == "github":
        result = await fetch_github_readme(entry["url"])
    else:
        return {"content": entry.get("raw_content", ""), "source": "stored"}

    if result.get("success"):
        return {"content": result["content"], "source": "fetched", "truncated": result.get("truncated", False)}
    raise HTTPException(status_code=502, detail=result.get("error", "Failed to fetch content"))


@router.get("/tags")
async def get_tags():
    return crud.get_all_tags()


@router.get("/stats")
async def get_stats():
    return crud.get_entry_count()


@router.post("/entries/github/auto-create")
async def auto_create_github_entry(repo_url: str):
    info_result = await fetch_github_info(repo_url)
    if not info_result.get("success"):
        raise HTTPException(status_code=400, detail=info_result.get("error", "Failed to fetch GitHub info"))

    readme_result = await fetch_github_readme(repo_url)
    raw_content = readme_result.get("content", "") if readme_result.get("success") else ""

    data = EntryCreate(
        url=repo_url,
        content_type="github",
        title=info_result.get("title", repo_url),
        raw_content=raw_content,
    )
    entry = crud.create_entry(data)
    return entry
