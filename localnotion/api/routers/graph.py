"""Knowledge graph API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from localnotion.api.deps import get_graph
from localnotion.api.schemas import GraphResponse

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("")
async def get_full_graph(workspace: Optional[str] = None) -> GraphResponse:
    graph = get_graph()
    data = graph.get_full_graph(workspace=workspace)
    return GraphResponse(**data)


@router.get("/{page_id}/neighborhood")
async def get_neighborhood(page_id: str, depth: int = Query(default=2, ge=1, le=5)) -> GraphResponse:
    graph = get_graph()
    data = graph.get_neighborhood(page_id, depth=depth)
    return GraphResponse(**data)


@router.get("/{page_id}/backlinks")
async def get_backlinks(page_id: str) -> list[dict]:
    graph = get_graph()
    backlinks = graph.get_backlinks(page_id)
    return [b.model_dump() for b in backlinks]


@router.get("/orphans")
async def get_orphans() -> list[dict]:
    graph = get_graph()
    orphans = graph.find_orphans()
    return [p.model_dump() for p in orphans]


@router.get("/{page_id}/suggestions")
async def get_link_suggestions(page_id: str, limit: int = Query(default=10, ge=1, le=50)) -> list[dict]:
    graph = get_graph()
    suggestions = graph.suggest_links(page_id, limit=limit)
    return [s.model_dump() for s in suggestions]
