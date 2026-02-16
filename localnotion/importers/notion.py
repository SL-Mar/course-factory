"""Notion workspace importer — pages and databases via API."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx
import ulid as ulid_lib

from localnotion.core.models import Page
from localnotion.core.store import PageStore
from localnotion.core.index import PageIndex

logger = logging.getLogger(__name__)

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionImporter:
    """Import a Notion workspace into LocalNotion."""

    def __init__(self, token: str, store: PageStore, index: PageIndex) -> None:
        self.token = token
        self.store = store
        self.index = index
        self._id_map: dict[str, str] = {}  # notion_id → localnotion_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def import_workspace(self, workspace: str = "notion-import") -> dict[str, int]:
        """Import all pages and databases from Notion."""
        stats = {"pages": 0, "databases": 0, "errors": 0}

        async with httpx.AsyncClient(timeout=30.0, headers=self.headers) as client:
            # Import pages
            pages = await self._search(client, filter_type="page")
            for notion_page in pages:
                try:
                    await self._import_page(client, notion_page, workspace)
                    stats["pages"] += 1
                except Exception:
                    logger.warning("Failed to import page %s", notion_page.get("id"), exc_info=True)
                    stats["errors"] += 1

            # Import databases
            databases = await self._search(client, filter_type="database")
            for db in databases:
                try:
                    await self._import_database(client, db, workspace)
                    stats["databases"] += 1
                except Exception:
                    logger.warning("Failed to import database %s", db.get("id"), exc_info=True)
                    stats["errors"] += 1

        logger.info("Notion import complete: %s", stats)
        return stats

    async def _search(self, client: httpx.AsyncClient, filter_type: str) -> list[dict]:
        """Search all objects of a given type."""
        results: list[dict] = []
        has_more = True
        start_cursor = None

        while has_more:
            body: dict[str, Any] = {"filter": {"value": filter_type, "property": "object"}, "page_size": 100}
            if start_cursor:
                body["start_cursor"] = start_cursor

            resp = await client.post(f"{NOTION_API}/search", json=body)
            if resp.status_code != 200:
                logger.error("Notion search failed: %s", resp.text)
                break

            data = resp.json()
            results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        return results

    async def _import_page(self, client: httpx.AsyncClient, notion_page: dict, workspace: str) -> None:
        """Convert a Notion page to a LocalNotion page."""
        notion_id = notion_page["id"]
        title = self._extract_title(notion_page)

        # Fetch blocks (content)
        blocks = await self._get_blocks(client, notion_id)
        content = self._blocks_to_markdown(blocks)

        # Map parent
        parent_id = None
        parent = notion_page.get("parent", {})
        if parent.get("type") == "page_id":
            parent_id = self._id_map.get(parent["page_id"])

        # Extract metadata
        created = notion_page.get("created_time", datetime.now(timezone.utc).isoformat())
        modified = notion_page.get("last_edited_time", created)

        page_id = str(ulid_lib.ULID())
        self._id_map[notion_id] = page_id

        tags = self._extract_tags(notion_page)

        page = Page(
            id=page_id,
            title=title,
            content=content,
            parent_id=parent_id,
            type="page",
            status="active",
            tags=tags,
            workspace=workspace,
            created_at=datetime.fromisoformat(created.replace("Z", "+00:00")),
            modified_at=datetime.fromisoformat(modified.replace("Z", "+00:00")),
        )
        page.word_count = page.compute_word_count()

        self.store.save(page)
        self.index.upsert_page(page)

    async def _get_blocks(self, client: httpx.AsyncClient, page_id: str) -> list[dict]:
        """Fetch all blocks for a page."""
        blocks: list[dict] = []
        has_more = True
        start_cursor = None

        while has_more:
            url = f"{NOTION_API}/blocks/{page_id}/children?page_size=100"
            if start_cursor:
                url += f"&start_cursor={start_cursor}"

            resp = await client.get(url)
            if resp.status_code != 200:
                break

            data = resp.json()
            blocks.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        return blocks

    async def _import_database(self, client: httpx.AsyncClient, db: dict, workspace: str) -> None:
        """Import a Notion database as a LocalNotion page describing the schema."""
        title = self._extract_db_title(db)
        properties = db.get("properties", {})

        content = f"# {title}\n\n**Imported Notion Database**\n\n## Properties\n\n"
        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "unknown")
            content += f"- **{prop_name}**: {prop_type}\n"

        page_id = str(ulid_lib.ULID())
        self._id_map[db["id"]] = page_id

        page = Page(
            id=page_id,
            title=f"[DB] {title}",
            content=content,
            type="note",
            status="active",
            tags=["notion-import", "database"],
            workspace=workspace,
        )
        page.word_count = page.compute_word_count()
        self.store.save(page)
        self.index.upsert_page(page)

    @staticmethod
    def _extract_title(page: dict) -> str:
        props = page.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "title":
                title_parts = prop.get("title", [])
                return "".join(t.get("plain_text", "") for t in title_parts) or "Untitled"
        return "Untitled"

    @staticmethod
    def _extract_db_title(db: dict) -> str:
        title_parts = db.get("title", [])
        return "".join(t.get("plain_text", "") for t in title_parts) or "Untitled Database"

    @staticmethod
    def _extract_tags(page: dict) -> list[str]:
        tags: list[str] = []
        props = page.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "multi_select":
                for opt in prop.get("multi_select", []):
                    tags.append(opt.get("name", ""))
            elif prop.get("type") == "select":
                sel = prop.get("select")
                if sel:
                    tags.append(sel.get("name", ""))
        return [t for t in tags if t]

    @staticmethod
    def _blocks_to_markdown(blocks: list[dict]) -> str:
        """Convert Notion blocks to markdown."""
        lines: list[str] = []
        for block in blocks:
            bt = block.get("type", "")
            data = block.get(bt, {})

            if bt.startswith("heading_"):
                level = int(bt[-1])
                text = _rich_text(data)
                lines.append(f"{'#' * level} {text}")
            elif bt == "paragraph":
                lines.append(_rich_text(data))
            elif bt == "bulleted_list_item":
                lines.append(f"- {_rich_text(data)}")
            elif bt == "numbered_list_item":
                lines.append(f"1. {_rich_text(data)}")
            elif bt == "to_do":
                checked = "x" if data.get("checked") else " "
                lines.append(f"- [{checked}] {_rich_text(data)}")
            elif bt == "code":
                lang = data.get("language", "")
                lines.append(f"```{lang}\n{_rich_text(data)}\n```")
            elif bt == "quote":
                lines.append(f"> {_rich_text(data)}")
            elif bt == "divider":
                lines.append("---")
            elif bt == "callout":
                icon = data.get("icon", {}).get("emoji", "")
                lines.append(f"> {icon} {_rich_text(data)}")
            elif bt == "toggle":
                lines.append(f"<details><summary>{_rich_text(data)}</summary></details>")
            elif bt == "image":
                url = data.get("file", {}).get("url", "") or data.get("external", {}).get("url", "")
                lines.append(f"![image]({url})")
            else:
                text = _rich_text(data)
                if text:
                    lines.append(text)

            lines.append("")

        return "\n".join(lines).strip()


def _rich_text(block_data: dict) -> str:
    """Extract plain text from Notion rich_text array."""
    parts = block_data.get("rich_text", [])
    return "".join(p.get("plain_text", "") for p in parts)
