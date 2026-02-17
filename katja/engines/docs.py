"""Docs engine — generate documentation from codebase + specs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import ulid as ulid_lib

from katja.core.models import Page
from katja.engines.base import Engine, EngineContext

logger = logging.getLogger(__name__)

DOCS_PROMPT = """You are a documentation writer. Generate clear product documentation.

Product: {product}
Source material:
{context}

Generate documentation with:
1. Overview / Getting Started
2. Installation / Setup
3. Key concepts and architecture
4. API reference (if applicable)
5. Configuration options
6. Examples and tutorials
7. Troubleshooting / FAQ

Use markdown with clear headings, code blocks, and tables where appropriate.
"""


class DocsEngine(Engine):
    """Generate product documentation from specs and code."""

    @property
    def name(self) -> str:
        return "docs"

    @property
    def display_name(self) -> str:
        return "Docs Engine"

    async def execute(self, ctx: EngineContext, **kwargs: Any) -> dict[str, Any]:
        product = kwargs.get("product", "")

        if not product:
            return {"error": "Product name is required"}

        ctx.data["started_at"] = datetime.now(timezone.utc).isoformat()
        ctx.report(f"Generating docs for: {product}")

        # Gather specs and existing docs
        context_pages = ctx.index.list_pages(workspace=ctx.workspace, limit=20)
        context_text = ""
        for p in context_pages:
            try:
                page = ctx.store.load(p.id)
                context_text += f"\n---\n**{page.title}** ({page.type})\n{page.content[:1500]}\n"
            except FileNotFoundError:
                pass

        prompt = DOCS_PROMPT.format(product=product, context=context_text or "No source material found.")

        ctx.report("Generating documentation with LLM...")
        result = await ctx.router.chat(
            "docs_generation",
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=8192,
        )

        ctx.tokens_used += result.usage.total_tokens

        page_id = str(ulid_lib.ULID())
        title = f"{product} — Documentation"
        page = Page(
            id=page_id,
            title=title,
            content=result.text,
            type="page",
            status="draft",
            tags=["docs", product.lower()],
            workspace=ctx.workspace,
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc),
        )
        page.word_count = page.compute_word_count()

        ctx.store.save(page)
        ctx.index.upsert_page(page)
        ctx.output_page_ids.append(page_id)

        ctx.report(f"Documentation generated: {title}")

        run = self.create_run_record(ctx, status="completed")
        ctx.index.save_engine_run(run)

        return {"page_id": page_id, "title": title, "word_count": page.word_count}
