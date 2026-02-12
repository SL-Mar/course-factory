"""Knowledge ingestion stage — fetch sources and save to workspace."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from course_factory.pipeline.stage import Stage

logger = logging.getLogger(__name__)


class KnowledgeStage(Stage):
    """Fetch all configured sources and store them as markdown files."""

    @property
    def name(self) -> str:
        return "knowledge"

    async def validate(self, context: dict) -> bool:
        return "sources" in context and "workspace_dir" in context

    async def execute(self, context: dict) -> dict:
        from course_factory.knowledge.fetcher import (
            fetch_notion_page,
            fetch_github_repo,
            fetch_url,
        )

        sources = context["sources"]
        workspace_dir = Path(context["workspace_dir"])
        knowledge_dir = workspace_dir / "01-knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)

        settings = context.get("settings", {})
        notion_key = settings.get("notion_api_key", "")
        gh_token = settings.get("github_token", "")

        results: list[dict] = []

        for src in sources:
            src_type = src.get("type", "")
            logger.info("Fetching source: %s", src)

            if src_type == "notion":
                page_id = src.get("id", "")
                result = fetch_notion_page(page_id, notion_key)
            elif src_type == "github":
                owner = src.get("owner", "")
                repo = src.get("repo", "")
                result = fetch_github_repo(owner, repo, gh_token)
            elif src_type == "url":
                url = src.get("url", "")
                result = fetch_url(url)
            else:
                logger.warning("Unknown source type: %s", src_type)
                continue

            if result.error:
                logger.warning("Fetch error for %s: %s", result.slug, result.error)
                # Still save a placeholder file
                content = f"# Fetch Error\n\nSource: {src}\nError: {result.error}\n"
                out_path = knowledge_dir / f"{result.slug}.md"
                out_path.write_text(content, encoding="utf-8")
            else:
                out_path = knowledge_dir / f"{result.slug}.md"
                out_path.write_text(result.content, encoding="utf-8")
                logger.info(
                    "Saved %s (%d chars)", out_path.name, len(result.content)
                )

            results.append({
                "type": result.source_type,
                "slug": result.slug,
                "file": str(out_path.relative_to(workspace_dir)),
                "chars": len(result.content),
                "error": result.error,
                "metadata": result.metadata,
            })

        # Write sources manifest
        manifest_path = knowledge_dir / "_sources.json"
        manifest_path.write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )

        context["knowledge_sources"] = results
        return context
