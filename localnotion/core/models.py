"""Core data models for LocalNotion pages and knowledge graph."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class Page(BaseModel):
    """A single knowledge page backed by a markdown file."""

    id: str = Field(..., description="ULID identifier")
    title: str = Field(..., min_length=1, max_length=1000)
    content: str = Field(default="", description="Markdown body (no frontmatter)")
    parent_id: Optional[str] = Field(default=None, description="Parent page ULID")
    type: str = Field(default="page", pattern=r"^(page|spec|article|note|journal)$")
    status: str = Field(default="draft", pattern=r"^(draft|active|archived)$")
    tags: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list, description="Outgoing page IDs")
    workspace: str = Field(default="default")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    word_count: int = Field(default=0, ge=0)
    is_deleted: bool = False
    icon: str = Field(default="", max_length=8)
    cover: str = Field(default="", max_length=500, description="CSS gradient or image URL")
    is_favorite: bool = False

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v

    def compute_word_count(self) -> int:
        return len(self.content.split())

    def extract_wiki_links(self) -> list[str]:
        """Extract [[page-id]] or [[page-title]] references."""
        return re.findall(r"\[\[([^\]]+)\]\]", self.content)


class PageSummary(BaseModel):
    """Lightweight page metadata for listings and search results."""

    id: str
    title: str
    type: str = "page"
    status: str = "draft"
    tags: list[str] = Field(default_factory=list)
    workspace: str = "default"
    parent_id: Optional[str] = None
    icon: str = ""
    cover: str = ""
    is_favorite: bool = False
    is_deleted: bool = False
    word_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SearchResult(BaseModel):
    """A single semantic search hit."""

    page_id: str
    title: str
    chunk_text: str
    score: float
    tags: list[str] = Field(default_factory=list)
    page_type: str = "page"


class BacklinkEntry(BaseModel):
    """A backlink reference."""

    source_id: str
    source_title: str
    context: str = ""
