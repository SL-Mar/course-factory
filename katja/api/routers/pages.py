"""Page CRUD + search API endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import asyncio

import ulid as ulid_lib
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import Response

from katja.api.deps import get_store, get_index, get_vector
from katja.api.schemas import (
    PageCreateRequest,
    PageUpdateRequest,
    PageResponse,
    PageListResponse,
    SearchRequest,
    SearchResultResponse,
    WorkspaceMetaRequest,
    WorkspaceMetaResponse,
    ReorderRequest,
)
from katja.core.models import Page

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
        sort_order=page.sort_order,
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


@router.get("/workspaces/meta")
async def list_workspace_meta() -> list[WorkspaceMetaResponse]:
    index = get_index()
    meta_rows = index.list_workspace_meta()
    meta_map = {m["name"]: m for m in meta_rows}

    # Build response with page counts from all known workspaces
    workspaces = index.get_workspaces()
    result: list[WorkspaceMetaResponse] = []
    seen: set[str] = set()

    # First: workspaces with metadata (in sort order)
    for m in meta_rows:
        count = index.count_pages(workspace=m["name"])
        result.append(WorkspaceMetaResponse(
            name=m["name"],
            icon=m["icon"],
            color=m["color"],
            sort_order=m["sort_order"],
            page_count=count,
        ))
        seen.add(m["name"])

    # Then: workspaces without metadata (alphabetical)
    for ws in sorted(workspaces):
        if ws not in seen:
            count = index.count_pages(workspace=ws)
            result.append(WorkspaceMetaResponse(
                name=ws,
                page_count=count,
            ))

    return result


@router.post("/workspaces/meta")
async def upsert_workspace_meta(req: WorkspaceMetaRequest) -> WorkspaceMetaResponse:
    index = get_index()
    index.upsert_workspace_meta(
        name=req.name,
        icon=req.icon,
        color=req.color,
        sort_order=req.sort_order,
    )
    count = index.count_pages(workspace=req.name)
    return WorkspaceMetaResponse(
        name=req.name,
        icon=req.icon,
        color=req.color,
        sort_order=req.sort_order,
        page_count=count,
    )


@router.post("/reorder")
async def reorder_pages(req: ReorderRequest) -> dict:
    """Batch-update sort_order for a list of page IDs.

    If workspace is provided, also moves all pages to that workspace.
    """
    index = get_index()
    store = get_store()
    updated = index.batch_reorder(req.page_ids, workspace=req.workspace)

    # Also update workspace in the .md files if moving between workspaces
    if req.workspace is not None:
        for pid in req.page_ids:
            try:
                page = store.load(pid)
                if page.workspace != req.workspace:
                    page.workspace = req.workspace
                    store.save(page)
            except FileNotFoundError:
                continue

    return {"ok": True, "updated": updated}


@router.get("/{page_id}/export/pdf")
async def export_page_pdf(page_id: str) -> Response:
    store = get_store()
    try:
        page = store.load(page_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")

    from katja.core.pdf import convert_to_pdf
    pdf_bytes = convert_to_pdf(page.title, page.content)
    safe_title = "".join(c for c in page.title if c.isalnum() or c in " -_").strip()[:80]
    filename = f"{safe_title or 'page'}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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


# -- Reindex ----------------------------------------------------------------

_reindex_status: dict[str, Any] = {"running": False, "indexed": 0, "total": 0, "error": ""}


async def _run_reindex() -> None:
    """Background task: embed all pages into Qdrant."""
    global _reindex_status
    store = get_store()
    vector = get_vector()
    pages = store.list_all()
    _reindex_status = {"running": True, "indexed": 0, "total": len(pages), "error": ""}
    logger.info("Reindex started: %d pages", len(pages))
    try:
        for page in pages:
            if page.is_deleted:
                continue
            await vector.index_page(page)
            _reindex_status["indexed"] += 1
    except Exception as exc:
        _reindex_status["error"] = str(exc)
        logger.error("Reindex failed: %s", exc)
    finally:
        _reindex_status["running"] = False
        logger.info("Reindex complete: %d/%d pages", _reindex_status["indexed"], _reindex_status["total"])


@router.post("/reindex")
async def reindex_pages() -> dict[str, Any]:
    """Trigger full vector reindex of all pages (runs in background)."""
    if _reindex_status.get("running"):
        return {"status": "already_running", **_reindex_status}
    asyncio.create_task(_run_reindex())
    return {"status": "started", "message": "Reindex started in background"}


@router.get("/reindex/status")
async def reindex_status() -> dict[str, Any]:
    """Check reindex progress."""
    return _reindex_status
