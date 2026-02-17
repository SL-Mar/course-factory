"""Spec engine — generate technical specifications from a brief."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import ulid as ulid_lib

from katja.core.models import Page
from katja.engines.base import Engine, EngineContext

logger = logging.getLogger(__name__)

SPEC_PROMPT = """You are a technical specification writer. Generate a detailed spec document.

Input:
- Brief: {brief}
- Product/Context: {product}

Context from existing knowledge:
{context}

Generate a specification with these sections:
1. Objective (what and why)
2. Architecture (system design, components)
3. Data Model (key entities, relationships)
4. API Design (endpoints, request/response)
5. Implementation Plan (phases, priorities)
6. Testing Strategy
7. File Manifest (files to create/modify)

Use markdown formatting. Be specific and actionable.
"""


class SpecEngine(Engine):
    """Generate technical specifications from a brief + existing knowledge."""

    @property
    def name(self) -> str:
        return "spec"

    @property
    def display_name(self) -> str:
        return "Spec Engine"

    async def execute(self, ctx: EngineContext, **kwargs: Any) -> dict[str, Any]:
        brief = kwargs.get("brief", "")
        product = kwargs.get("product", "")

        if not brief:
            return {"error": "Brief is required"}

        ctx.data["started_at"] = datetime.now(timezone.utc).isoformat()
        ctx.report(f"Generating spec for: {brief}")

        # Gather context from related pages
        context_pages = ctx.index.search_titles(brief, limit=5)
        context_text = ""
        for p in context_pages:
            try:
                page = ctx.store.load(p.id)
                context_text += f"\n---\n**{page.title}**\n{page.content[:1500]}\n"
            except FileNotFoundError:
                pass

        prompt = SPEC_PROMPT.format(brief=brief, product=product, context=context_text or "No existing context found.")

        ctx.report("Generating specification with LLM...")
        result = await ctx.router.chat(
            "spec_writing",
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=8192,
        )

        ctx.tokens_used += result.usage.total_tokens

        # Create a new page with the spec
        page_id = str(ulid_lib.ULID())
        title = f"SPEC — {brief}"
        page = Page(
            id=page_id,
            title=title,
            content=result.text,
            type="spec",
            status="draft",
            tags=["spec", product] if product else ["spec"],
            workspace=ctx.workspace,
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc),
        )
        page.word_count = page.compute_word_count()

        ctx.store.save(page)
        ctx.index.upsert_page(page)
        ctx.output_page_ids.append(page_id)

        ctx.report(f"Spec created: {title}")

        run = self.create_run_record(ctx, status="completed")
        ctx.index.save_engine_run(run)

        return {"page_id": page_id, "title": title, "word_count": page.word_count}
