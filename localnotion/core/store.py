"""Markdown file store — pages as flat .md files with YAML frontmatter."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from localnotion.core.models import Page

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PageStore:
    """CRUD operations for markdown pages on disk.

    Storage layout::

        ~/localnotion/pages/
        ├── 01JKXYZ123456.md   # flat, ULID-named
        ├── 01JKXYZ123457.md
        └── ...
    """

    def __init__(self, data_dir: Path) -> None:
        self.pages_dir = data_dir / "pages"
        self.pages_dir.mkdir(parents=True, exist_ok=True)

    def _page_path(self, page_id: str) -> Path:
        safe = page_id.replace("/", "_").replace("\\", "_")
        return self.pages_dir / f"{safe}.md"

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    @staticmethod
    def page_to_markdown(page: Page) -> str:
        """Serialise a Page to markdown with YAML frontmatter."""
        fm: dict[str, Any] = {
            "id": page.id,
            "title": page.title,
            "created": page.created_at.isoformat(),
            "modified": page.modified_at.isoformat(),
            "tags": page.tags,
            "type": page.type,
            "status": page.status,
            "workspace": page.workspace,
        }
        if page.parent_id:
            fm["parent"] = page.parent_id
        if page.links:
            fm["links"] = page.links
        if page.icon:
            fm["icon"] = page.icon
        if page.cover:
            fm["cover"] = page.cover
        if page.is_favorite:
            fm["favorite"] = True
        if page.is_deleted:
            fm["deleted"] = True

        frontmatter = yaml.dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
        return f"---\n{frontmatter}---\n\n{page.content}"

    @staticmethod
    def markdown_to_page(text: str, file_path: Path | None = None) -> Page:
        """Parse a markdown file with frontmatter into a Page."""
        match = _FRONTMATTER_RE.match(text)
        if not match:
            raise ValueError(f"No valid YAML frontmatter found in {file_path or 'input'}")

        fm = yaml.safe_load(match.group(1)) or {}
        content = text[match.end():].strip()

        created = fm.get("created", _now_iso())
        modified = fm.get("modified", _now_iso())
        if isinstance(created, datetime):
            created = created.isoformat()
        if isinstance(modified, datetime):
            modified = modified.isoformat()

        return Page(
            id=fm.get("id", ""),
            title=fm.get("title", "Untitled"),
            content=content,
            parent_id=fm.get("parent"),
            type=fm.get("type", "page"),
            status=fm.get("status", "draft"),
            tags=fm.get("tags", []),
            links=fm.get("links", []),
            workspace=fm.get("workspace", "default"),
            created_at=datetime.fromisoformat(created),
            modified_at=datetime.fromisoformat(modified),
            word_count=len(content.split()),
            icon=fm.get("icon", ""),
            cover=fm.get("cover", ""),
            is_favorite=fm.get("favorite", False),
            is_deleted=fm.get("deleted", False),
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save(self, page: Page) -> Path:
        """Write page to disk as markdown with frontmatter."""
        page.word_count = page.compute_word_count()
        page.modified_at = datetime.now(timezone.utc)
        page.links = page.extract_wiki_links()

        path = self._page_path(page.id)
        path.write_text(self.page_to_markdown(page), encoding="utf-8")
        logger.debug("Saved page %s to %s", page.id, path)
        return path

    def load(self, page_id: str) -> Page:
        """Load a page from disk by ID."""
        path = self._page_path(page_id)
        if not path.is_file():
            raise FileNotFoundError(f"Page not found: {page_id}")
        text = path.read_text(encoding="utf-8")
        return self.markdown_to_page(text, path)

    def delete(self, page_id: str, soft: bool = True) -> None:
        """Delete a page. Soft-delete marks it; hard-delete removes the file."""
        if soft:
            page = self.load(page_id)
            page.is_deleted = True
            self.save(page)
        else:
            path = self._page_path(page_id)
            if path.is_file():
                path.unlink()
                logger.info("Hard-deleted page %s", page_id)

    def exists(self, page_id: str) -> bool:
        return self._page_path(page_id).is_file()

    def list_all(self) -> list[Page]:
        """Load all pages from disk."""
        pages: list[Page] = []
        for md_file in sorted(self.pages_dir.glob("*.md")):
            try:
                page = self.markdown_to_page(
                    md_file.read_text(encoding="utf-8"), md_file
                )
                pages.append(page)
            except Exception:
                logger.warning("Skipping corrupt page file: %s", md_file)
        return pages

    def list_active(self) -> list[Page]:
        """List non-deleted pages."""
        return [p for p in self.list_all() if not p.is_deleted]

    def search_text(self, query: str, limit: int = 50) -> list[Page]:
        """Simple full-text search across titles and content."""
        q = query.lower()
        results: list[Page] = []
        for page in self.list_active():
            if q in page.title.lower() or q in page.content.lower():
                results.append(page)
                if len(results) >= limit:
                    break
        return results
