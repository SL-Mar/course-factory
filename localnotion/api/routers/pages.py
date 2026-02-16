"""Page CRUD + search API endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import ulid as ulid_lib
from fastapi import APIRouter, HTTPException, Query

from localnotion.api.deps import get_store, get_index, get_vector
from localnotion.api.schemas import (
    PageCreateRequest,
    PageUpdateRequest,
    PageResponse,
    PageListResponse,
    SearchRequest,
    SearchResultResponse,
)
from localnotion.core.models import Page

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pages", tags=["pages"])


def _page_response(page: Page) -> PageResponse:
    """Convert a Page model to a frontend-compatible PageResponse."""
    return PageResponse(
        id=page.id,
        title=page.title,
        content=page.content,
        parent_id=page.parent_id,
        type=page.type,
        status=page.status,
        tags=page.tags,
        links=page.links,
        workspace=page.workspace,
        created_at=page.created_at.isoformat(),
        updated_at=page.modified_at.isoformat(),
        word_count=page.word_count,
        icon=page.icon,
        cover=page.cover,
        is_favorite=page.is_favorite,
        is_trashed=page.is_deleted,
    )


def _summary_to_dict(summary: Any) -> dict[str, Any]:
    """Convert a PageSummary to frontend-compatible dict."""
    d = summary.model_dump()
    # Rename modified_at → updated_at for frontend
    if "modified_at" in d:
        val = d.pop("modified_at")
        d["updated_at"] = val.isoformat() if isinstance(val, datetime) else str(val)
    if "created_at" in d:
        val = d["created_at"]
        d["created_at"] = val.isoformat() if isinstance(val, datetime) else str(val)
    # Map is_deleted → is_trashed
    d["is_trashed"] = d.pop("is_deleted", False)
    # Ensure cover exists
    if "cover" not in d:
        d["cover"] = ""
    return d


@router.get("")
async def list_pages(
    workspace: Optional[str] = None,
    type: Optional[str] = None,
    parent_id: Optional[str] = None,
    favorites: bool = False,
    include_trashed: bool = False,
    limit: int = Query(default=1000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> PageListResponse:
    index = get_index()
    pages = index.list_pages(
        workspace=workspace,
        page_type=type,
        parent_id=parent_id,
        favorites_only=favorites,
        limit=limit,
        offset=offset,
    )
    total = index.count_pages(workspace=workspace)
    return PageListResponse(
        pages=[_summary_to_dict(p) for p in pages],
        total=total,
    )


@router.get("/recent")
async def recent_pages(limit: int = Query(default=20, ge=1, le=100)) -> PageListResponse:
    index = get_index()
    pages = index.get_recent(limit=limit)
    return PageListResponse(pages=[_summary_to_dict(p) for p in pages])


@router.get("/workspaces")
async def list_workspaces() -> list[str]:
    return get_index().get_workspaces()


@router.get("/{page_id}")
async def get_page(page_id: str) -> PageResponse:
    store = get_store()
    try:
        page = store.load(page_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")
    return _page_response(page)


@router.post("", status_code=201)
async def create_page(req: PageCreateRequest) -> PageResponse:
    store = get_store()
    index = get_index()

    page_id = str(ulid_lib.ULID())
    now = datetime.now(timezone.utc)

    page = Page(
        id=page_id,
        title=req.title,
        content=req.content,
        parent_id=req.parent_id,
        type=req.type,
        tags=req.tags,
        workspace=req.workspace,
        icon=req.icon,
        cover=req.cover,
        created_at=now,
        modified_at=now,
    )
    page.word_count = page.compute_word_count()
    page.links = page.extract_wiki_links()

    store.save(page)
    index.upsert_page(page)

    # Index in vector store (fire and forget)
    try:
        vector = get_vector()
        import asyncio
        asyncio.create_task(vector.index_page(page))
    except Exception:
        pass

    return _page_response(page)


@router.patch("/{page_id}")
async def update_page(page_id: str, req: PageUpdateRequest) -> PageResponse:
    store = get_store()
    index = get_index()

    try:
        page = store.load(page_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")

    updates = req.model_dump(exclude_none=True)

    # Map frontend field names to backend model fields
    if "is_trashed" in updates:
        updates["is_deleted"] = updates.pop("is_trashed")

    for key, value in updates.items():
        setattr(page, key, value)

    page.word_count = page.compute_word_count()
    page.links = page.extract_wiki_links()

    store.save(page)
    index.upsert_page(page)

    try:
        vector = get_vector()
        import asyncio
        asyncio.create_task(vector.index_page(page))
    except Exception:
        pass

    return _page_response(page)


@router.delete("/{page_id}")
async def delete_page(page_id: str, hard: bool = False) -> dict:
    store = get_store()
    index = get_index()

    if not store.exists(page_id):
        raise HTTPException(status_code=404, detail="Page not found")

    store.delete(page_id, soft=not hard)
    if hard:
        index.remove_page(page_id)
    else:
        page = store.load(page_id)
        index.upsert_page(page)

    return {"ok": True}


@router.post("/search")
async def search_pages(req: SearchRequest) -> SearchResultResponse:
    """Semantic search via vector index, with full-text fallback."""
    vector = get_vector()
    results = await vector.search(
        query=req.query,
        limit=req.limit,
        workspace=req.workspace,
        page_type=req.page_type,
    )

    if results:
        return SearchResultResponse(results=[r.model_dump() for r in results])

    # Fallback to title search
    index = get_index()
    title_results = index.search_titles(req.query, limit=req.limit)
    return SearchResultResponse(
        results=[{"page_id": p.id, "title": p.title, "score": 1.0, "chunk_text": "", "tags": p.tags} for p in title_results]
    )
