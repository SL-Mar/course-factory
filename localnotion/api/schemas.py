"""Pydantic schemas for the LocalNotion API."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# -- Pages -------------------------------------------------------------------

class PageCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=1000)
    content: str = ""
    parent_id: Optional[str] = None
    type: str = "page"
    tags: list[str] = Field(default_factory=list)
    workspace: str = "default"
    icon: str = ""
    cover: str = ""

class PageUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    parent_id: Optional[str] = Field(default=None)
    type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None
    workspace: Optional[str] = None
    icon: Optional[str] = None
    cover: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_trashed: Optional[bool] = None
    sort_order: Optional[int] = None

class PageResponse(BaseModel):
    id: str
    title: str
    content: str = ""
    parent_id: Optional[str] = None
    type: str = "page"
    status: str = "draft"
    tags: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    workspace: str = "default"
    created_at: str = ""
    updated_at: str = ""
    word_count: int = 0
    icon: str = ""
    cover: str = ""
    is_favorite: bool = False
    is_trashed: bool = False
    sort_order: int = 0

class PageListResponse(BaseModel):
    pages: list[dict[str, Any]]
    total: int = 0


# -- Workspace Meta ----------------------------------------------------------

class WorkspaceMetaRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: str = Field(default="", max_length=8)
    color: str = Field(default="#2383e2", max_length=100)
    sort_order: int = 0

class WorkspaceMetaResponse(BaseModel):
    name: str
    icon: str = ""
    color: str = "#2383e2"
    sort_order: int = 0
    page_count: int = 0


class ReorderRequest(BaseModel):
    page_ids: list[str] = Field(..., min_length=1, max_length=500)
    workspace: Optional[str] = None


# -- Search ------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    workspace: Optional[str] = None
    page_type: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)

class SearchResultResponse(BaseModel):
    results: list[dict[str, Any]]


# -- Graph -------------------------------------------------------------------

class GraphResponse(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


# -- Tables ------------------------------------------------------------------

class TableCreateRequest(BaseModel):
    template: Optional[str] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    columns: Optional[list[dict[str, Any]]] = None

class RowCreateRequest(BaseModel):
    data: dict[str, Any]
    page_id: Optional[str] = None

class RowUpdateRequest(BaseModel):
    data: dict[str, Any]

class TableQueryRequest(BaseModel):
    where: Optional[dict[str, Any]] = None
    order_by: Optional[str] = None
    order_dir: str = "asc"
    limit: int = 200
    offset: int = 0


# -- AI Chat -----------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    include_context: bool = True

class ChatResponse(BaseModel):
    response: str
    context_pages: list[str] = Field(default_factory=list)

class SlashCommandRequest(BaseModel):
    command: str = Field(..., min_length=1)
    page_id: str = ""
    page_content: str = ""
    page_title: str = ""


# -- Engines -----------------------------------------------------------------

class EngineRunRequest(BaseModel):
    engine: str = Field(..., pattern="^(course|spec|article|docs)$")
    workspace: str = "default"
    params: dict[str, Any] = Field(default_factory=dict)

class EngineStatusResponse(BaseModel):
    status: str = "idle"
    message: str = ""
    result: Optional[dict[str, Any]] = None


# -- Import ------------------------------------------------------------------

class NotionImportRequest(BaseModel):
    token: str = Field(..., min_length=1)
    workspace: str = "notion-import"

class MarkdownImportRequest(BaseModel):
    source_dir: str = Field(..., min_length=1)
    workspace: str = "imported"
    recursive: bool = True


# -- Setup -------------------------------------------------------------------

class TestConnectionRequest(BaseModel):
    service: str = Field(..., pattern="^(ollama|qdrant)$")
    url: str

class SaveConfigRequest(BaseModel):
    license_key: str = ""
    ollama_url: str = "http://localhost:11434"
    qdrant_url: str = "http://localhost:6333"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    telegram_webhook: str = ""
    notion_api_key: str = ""
    ollama_model: str = "qwen2.5:14b"
    embed_model: str = "nomic-embed-text"
    cloud_provider: str = "anthropic"
    cloud_model: str = "claude-sonnet-4-5-20250929"

class ConnectionResult(BaseModel):
    ok: bool
    service: str
    message: str
    details: Optional[dict] = None

class SaveResult(BaseModel):
    ok: bool
    path: str = ""
    error: str = ""

class LicenseInfo(BaseModel):
    valid: bool
    email: str = ""
    product: str = ""
    tier: str = ""
    expiry: str = ""
    is_expired: bool = False
    error: str = ""
