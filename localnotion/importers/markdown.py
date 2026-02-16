"""Markdown/Obsidian vault importer."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ulid as ulid_lib

from localnotion.core.models import Page
from localnotion.core.store import PageStore
from localnotion.core.index import PageIndex

logger = logging.getLogger(__name__)


class MarkdownImporter:
    """Import a directory of markdown files into LocalNotion."""

    def __init__(self, store: PageStore, index: PageIndex) -> None:
        self.store = store
        self.index = index

    def import_directory(
        self,
        source_dir: str | Path,
        workspace: str = "imported",
        recursive: bool = True,
    ) -> dict[str, int]:
        """Import all .md files from a directory."""
        source = Path(source_dir)
        if not source.is_dir():
            raise FileNotFoundError(f"Directory not found: {source}")

        stats = {"imported": 0, "skipped": 0, "errors": 0}
        pattern = "**/*.md" if recursive else "*.md"

        for md_file in sorted(source.glob(pattern)):
            try:
                self._import_file(md_file, workspace, source)
                stats["imported"] += 1
            except Exception:
                logger.warning("Failed to import %s", md_file, exc_info=True)
                stats["errors"] += 1

        logger.info("Markdown import complete: %s", stats)
        return stats

    def _import_file(self, file_path: Path, workspace: str, root: Path) -> None:
        """Import a single markdown file."""
        text = file_path.read_text(encoding="utf-8")

        # Try to parse as LocalNotion page with frontmatter
        try:
            page = PageStore.markdown_to_page(text, file_path)
            if not page.id:
                page.id = str(ulid_lib.ULID())
            page.workspace = workspace
        except (ValueError, Exception):
            # No frontmatter — create a new page from raw markdown
            title = file_path.stem.replace("-", " ").replace("_", " ").title()
            page_id = str(ulid_lib.ULID())

            # Derive tags from directory structure
            rel = file_path.relative_to(root)
            tags = [p for p in rel.parts[:-1] if p] + [workspace]

            page = Page(
                id=page_id,
                title=title,
                content=text,
                type="note",
                status="active",
                tags=tags,
                workspace=workspace,
                created_at=datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc),
                modified_at=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
            )

        page.word_count = page.compute_word_count()

        # Convert Obsidian [[links]] to LocalNotion format (already compatible)
        # Obsidian uses [[Note Name]], LocalNotion uses the same syntax

        self.store.save(page)
        self.index.upsert_page(page)
