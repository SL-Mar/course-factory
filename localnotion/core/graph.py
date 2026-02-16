"""Knowledge graph — bidirectional links, backlinks, entity extraction."""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from localnotion.core.index import PageIndex
from localnotion.core.models import BacklinkEntry, PageSummary

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """Bidirectional link graph built from [[wiki-links]] in page content."""

    def __init__(self, index: PageIndex) -> None:
        self.index = index

    @staticmethod
    def extract_links(content: str) -> list[str]:
        """Find all [[page-id]] or [[page-title]] references in markdown."""
        return re.findall(r"\[\[([^\]]+)\]\]", content)

    def get_backlinks(self, page_id: str) -> list[BacklinkEntry]:
        """All pages that link TO this page."""
        return self.index.get_backlinks(page_id)

    def get_forward_links(self, page_id: str) -> list[PageSummary]:
        """All pages that this page links TO."""
        summary = self.index.get_page_summary(page_id)
        if not summary:
            return []
        # The page's links are stored in the page_index
        from localnotion.core.index import json
        row = self.index._conn.execute(
            "SELECT links FROM page_index WHERE id = ?", (page_id,)
        ).fetchone()
        if not row or not row["links"]:
            return []
        link_ids = json.loads(row["links"])
        results = []
        for lid in link_ids:
            s = self.index.get_page_summary(lid)
            if s:
                results.append(s)
        return results

    def get_neighborhood(self, page_id: str, depth: int = 2) -> dict[str, Any]:
        """Return local subgraph around a page for visualization.

        Returns a dict with 'nodes' and 'edges' suitable for D3 force graph.
        """
        visited: set[str] = set()
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, str]] = []

        def _traverse(pid: str, current_depth: int) -> None:
            if pid in visited or current_depth > depth:
                return
            visited.add(pid)

            summary = self.index.get_page_summary(pid)
            if not summary:
                return

            nodes.append({
                "id": pid,
                "title": summary.title,
                "type": summary.type,
                "workspace": summary.workspace,
            })

            # Forward links
            row = self.index._conn.execute(
                "SELECT links FROM page_index WHERE id = ?", (pid,)
            ).fetchone()
            if row and row["links"]:
                import json
                for target in json.loads(row["links"]):
                    edges.append({"source": pid, "target": target})
                    _traverse(target, current_depth + 1)

            # Backlinks
            for bl in self.index.get_backlinks(pid):
                edges.append({"source": bl.source_id, "target": pid})
                _traverse(bl.source_id, current_depth + 1)

        _traverse(page_id, 0)
        return {"nodes": nodes, "edges": edges}

    def find_orphans(self) -> list[PageSummary]:
        """Pages with no incoming or outgoing links."""
        return self.index.get_orphans()

    def suggest_links(self, page_id: str, limit: int = 10) -> list[PageSummary]:
        """Suggest pages that might be related (based on shared tags/workspace)."""
        summary = self.index.get_page_summary(page_id)
        if not summary:
            return []

        # Simple heuristic: same workspace + overlapping tags
        candidates = self.index.list_pages(workspace=summary.workspace, limit=100)
        scored: list[tuple[float, PageSummary]] = []
        my_tags = set(summary.tags)

        for c in candidates:
            if c.id == page_id:
                continue
            overlap = len(my_tags & set(c.tags))
            if overlap > 0:
                scored.append((overlap, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:limit]]

    def get_full_graph(self, workspace: Optional[str] = None) -> dict[str, Any]:
        """Return the full knowledge graph for visualization."""
        pages = self.index.list_pages(workspace=workspace, limit=5000)
        nodes = [
            {"id": p.id, "title": p.title, "type": p.type, "workspace": p.workspace}
            for p in pages
        ]

        import json
        edges: list[dict[str, str]] = []
        for p in pages:
            row = self.index._conn.execute(
                "SELECT links FROM page_index WHERE id = ?", (p.id,)
            ).fetchone()
            if row and row["links"]:
                for target in json.loads(row["links"]):
                    edges.append({"source": p.id, "target": target})

        return {"nodes": nodes, "edges": edges}
