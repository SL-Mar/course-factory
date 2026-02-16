"""Knowledge graph API endpoints."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Query

from localnotion.api.deps import get_graph, get_index
from localnotion.api.schemas import GraphResponse

router = APIRouter(prefix="/api/graph", tags=["graph"])


def _enrich_graph(data: dict) -> dict:
    """Rename edges→links and add tags/link_count to nodes."""
    index = get_index()
    edges = data.get("edges", [])
    nodes = data.get("nodes", [])

    # Count outgoing links per node
    link_counts: dict[str, int] = {}
    for edge in edges:
        src = edge.get("source", "")
        link_counts[src] = link_counts.get(src, 0) + 1

    # Enrich nodes with tags and link_count
    enriched_nodes = []
    for node in nodes:
        pid = node["id"]
        row = index._conn.execute(
            "SELECT tags FROM page_index WHERE id = ?", (pid,)
        ).fetchone()
        tags = json.loads(row["tags"]) if row and row["tags"] else []
        enriched_nodes.append({
            **node,
            "tags": tags,
            "link_count": link_counts.get(pid, 0),
        })

    return {"nodes": enriched_nodes, "links": edges}


@router.get("")
async def get_full_graph(workspace: Optional[str] = None) -> GraphResponse:
    graph = get_graph()
    data = graph.get_full_graph(workspace=workspace)
    return GraphResponse(**_enrich_graph(data))


@router.get("/{page_id}/neighborhood")
async def get_neighborhood(page_id: str, depth: int = Query(default=2, ge=1, le=5)) -> GraphResponse:
    graph = get_graph()
    data = graph.get_neighborhood(page_id, depth=depth)
    return GraphResponse(**_enrich_graph(data))


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
