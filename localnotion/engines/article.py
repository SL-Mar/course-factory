"""Article engine — draft technical articles from notes and research."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import ulid as ulid_lib

from localnotion.core.models import Page
from localnotion.engines.base import Engine, EngineContext

logger = logging.getLogger(__name__)

ARTICLE_PROMPT = """You are a technical writer drafting an article.

Topic: {topic}
Target audience: {audience}

Context from the knowledge base:
{context}

Write a compelling technical article with:
1. An engaging introduction / hook
2. Clear section headings
3. Technical depth with practical examples
4. Code snippets where relevant
5. Diagrams described in Mermaid notation (```mermaid blocks)
6. A conclusion with key takeaways

Write in a professional but approachable style. Use markdown formatting.
"""


class ArticleEngine(Engine):
    """Draft technical articles from existing knowledge."""

    @property
    def name(self) -> str:
        return "article"

    @property
    def display_name(self) -> str:
        return "Article Engine"

    async def execute(self, ctx: EngineContext, **kwargs: Any) -> dict[str, Any]:
        topic = kwargs.get("topic", "")
        audience = kwargs.get("audience", "technical professionals")

        if not topic:
            return {"error": "Topic is required"}

        ctx.data["started_at"] = datetime.now(timezone.utc).isoformat()
        ctx.report(f"Drafting article: {topic}")

        # Gather context
        context_pages = ctx.index.search_titles(topic, limit=8)
        context_text = ""
        for p in context_pages:
            try:
                page = ctx.store.load(p.id)
                context_text += f"\n---\n**{page.title}**\n{page.content[:2000]}\n"
            except FileNotFoundError:
                pass

        prompt = ARTICLE_PROMPT.format(
            topic=topic, audience=audience, context=context_text or "No existing context found."
        )

        ctx.report("Generating article draft with LLM...")
        result = await ctx.router.chat(
            "article_drafting",
            [{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=8192,
        )

        ctx.tokens_used += result.usage.total_tokens

        page_id = str(ulid_lib.ULID())
        title = topic
        page = Page(
            id=page_id,
            title=title,
            content=result.text,
            type="article",
            status="draft",
            tags=["article", "draft"],
            workspace=ctx.workspace,
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc),
        )
        page.word_count = page.compute_word_count()

        ctx.store.save(page)
        ctx.index.upsert_page(page)
        ctx.output_page_ids.append(page_id)

        ctx.report(f"Article drafted: {title}")

        run = self.create_run_record(ctx, status="completed")
        ctx.index.save_engine_run(run)

        return {"page_id": page_id, "title": title, "word_count": page.word_count}
