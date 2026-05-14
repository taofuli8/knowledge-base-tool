from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EntryCreate(BaseModel):
    url: Optional[str] = ""
    content_type: str
    raw_content: Optional[str] = ""
    title: Optional[str] = ""

    def model_post_init(self, __context):
        if self.content_type not in ("url", "tutorial", "github"):
            raise ValueError("content_type must be 'url', 'tutorial', or 'github'")
        if self.content_type == "url" and not self.url:
            raise ValueError("url is required for content_type 'url'")
        if self.content_type == "tutorial" and not self.raw_content:
            raise ValueError("raw_content is required for content_type 'tutorial'")


class EntryUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    url: Optional[str] = None


class EntryResponse(BaseModel):
    id: int
    title: str
    url: str
    content_type: str
    summary: str
    tags: List[str]
    status: str
    created_at: str
    updated_at: str


class SearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[EntryResponse]


class TagCount(BaseModel):
    tag: str
    count: int
