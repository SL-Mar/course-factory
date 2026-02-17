"""Course engine — ported from Katja pipeline.

Transforms knowledge into a structured course (discovery → research → synthesis → production).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import ulid as ulid_lib

from katja.core.models import Page
from katja.engines.base import Engine, EngineContext

logger = logging.getLogger(__name__)

DISCOVERY_PROMPT = """You are a curriculum designer. Create a structured course outline.

Topic: {topic}
Source material:
{context}

Generate a JSON course structure:
{{
  "title": "Course Title",
  "description": "One-paragraph description",
  "modules": [
    {{
      "title": "Module 1 Title",
      "description": "Module description",
      "lessons": [
        {{"title": "Lesson 1.1", "objectives": ["obj1", "obj2"]}}
      ]
    }}
  ]
}}

Design 4-8 modules with 3-5 lessons each. Focus on practical, hands-on learning.
"""

RESEARCH_PROMPT = """You are a research assistant preparing course material.

Module: {module_title}
Module description: {module_desc}
Lesson: {lesson_title}
Learning objectives: {objectives}

Source context:
{context}

Write detailed research notes for this lesson covering:
1. Key concepts and definitions
2. Technical details and mechanisms
3. Practical examples and use cases
4. Common pitfalls and best practices
5. References and further reading

Use markdown formatting with clear sections.
"""

SCRIPT_PROMPT = """You are an instructor writing a lesson script.

Lesson: {lesson_title}
Research notes:
{research}

Write an instructor-style lesson script with:
1. Opening hook (engage the student)
2. Key concepts explained clearly
3. Step-by-step walkthrough
4. Practical examples with code (if relevant)
5. Summary and key takeaways
6. Transition to next lesson

Write in a conversational, engaging tone. Use markdown.
"""

SLIDE_PROMPT = """You are creating presentation slides for a lesson.

Lesson: {lesson_title}
Script:
{script}

Generate a Marp-compatible slide deck (.marp.md format):

---
marp: true
theme: default
paginate: true
---

# Slide Title

Content here

---

Create 8-15 slides with:
- Clear slide titles
- Bullet points (max 5 per slide)
- Code blocks where relevant
- Speaker notes (<!-- notes: ... -->)

Keep slides visual and uncluttered.
"""


class CourseEngine(Engine):
    """Full course generation pipeline: discovery → research → synthesis → production."""

    @property
    def name(self) -> str:
        return "course"

    @property
    def display_name(self) -> str:
        return "Course Engine"

    async def execute(self, ctx: EngineContext, **kwargs: Any) -> dict[str, Any]:
        topic = kwargs.get("topic", "")
        if not topic:
            return {"error": "Topic is required"}

        ctx.data["started_at"] = datetime.now(timezone.utc).isoformat()

        # Gather source material
        ctx.report("Gathering source material...")
        source_pages = ctx.index.search_titles(topic, limit=10)
        context = ""
        for p in source_pages:
            try:
                page = ctx.store.load(p.id)
                context += f"\n---\n**{page.title}**\n{page.content[:2000]}\n"
                ctx.data.setdefault("input_page_ids", []).append(p.id)
            except FileNotFoundError:
                pass

        # Stage 1: Discovery
        ctx.report("Stage 1/4: Discovering course structure...")
        discovery_result = await ctx.router.chat(
            "outline",
            [{"role": "user", "content": DISCOVERY_PROMPT.format(topic=topic, context=context or "No source material.")}],
            temperature=0.4,
        )
        ctx.tokens_used += discovery_result.usage.total_tokens

        # Save discovery as a page
        discovery_page = self._create_page(
            ctx, f"Course Discovery — {topic}", discovery_result.text, "note", ["course", "discovery"]
        )

        # Parse modules (best-effort JSON extraction)
        import json, re
        modules = []
        json_match = re.search(r"\{[\s\S]*\}", discovery_result.text)
        if json_match:
            try:
                structure = json.loads(json_match.group())
                modules = structure.get("modules", [])
            except json.JSONDecodeError:
                pass

        if not modules:
            ctx.report("Could not parse course structure. Discovery page saved.")
            return {"page_id": discovery_page.id, "title": discovery_page.title, "stages_completed": 1}

        # Stage 2: Research
        ctx.report(f"Stage 2/4: Researching {len(modules)} modules...")
        research_pages = []
        for i, module in enumerate(modules):
            for j, lesson in enumerate(module.get("lessons", [])):
                ctx.report(f"Researching: {lesson.get('title', f'Lesson {i+1}.{j+1}')}")
                result = await ctx.router.chat(
                    "research",
                    [{"role": "user", "content": RESEARCH_PROMPT.format(
                        module_title=module.get("title", ""),
                        module_desc=module.get("description", ""),
                        lesson_title=lesson.get("title", ""),
                        objectives=", ".join(lesson.get("objectives", [])),
                        context=context[:3000],
                    )}],
                    temperature=0.3,
                )
                ctx.tokens_used += result.usage.total_tokens
                page = self._create_page(
                    ctx,
                    f"Research — {lesson.get('title', '')}",
                    result.text,
                    "note",
                    ["course", "research", module.get("title", "").lower()[:30]],
                )
                research_pages.append((lesson, page, result.text))

        # Stage 3: Synthesis (scripts)
        ctx.report(f"Stage 3/4: Writing {len(research_pages)} lesson scripts...")
        script_pages = []
        for lesson, research_page, research_text in research_pages:
            ctx.report(f"Writing script: {lesson.get('title', '')}")
            result = await ctx.router.chat(
                "script_writing",
                [{"role": "user", "content": SCRIPT_PROMPT.format(
                    lesson_title=lesson.get("title", ""),
                    research=research_text[:4000],
                )}],
                temperature=0.5,
            )
            ctx.tokens_used += result.usage.total_tokens
            page = self._create_page(
                ctx, f"Script — {lesson.get('title', '')}", result.text, "note", ["course", "script"]
            )
            script_pages.append((lesson, page, result.text))

        # Stage 4: Production (slides)
        ctx.report(f"Stage 4/4: Generating {len(script_pages)} slide decks...")
        for lesson, script_page, script_text in script_pages:
            ctx.report(f"Creating slides: {lesson.get('title', '')}")
            result = await ctx.router.chat(
                "slide_generation",
                [{"role": "user", "content": SLIDE_PROMPT.format(
                    lesson_title=lesson.get("title", ""),
                    script=script_text[:4000],
                )}],
                temperature=0.4,
            )
            ctx.tokens_used += result.usage.total_tokens
            self._create_page(
                ctx, f"Slides — {lesson.get('title', '')}", result.text, "note", ["course", "slides"]
            )

        ctx.report("Course generation complete!")

        run = self.create_run_record(ctx, status="completed")
        ctx.index.save_engine_run(run)

        return {
            "discovery_page_id": discovery_page.id,
            "total_pages": len(ctx.output_page_ids),
            "modules": len(modules),
            "lessons": len(research_pages),
            "stages_completed": 4,
        }

    def _create_page(
        self, ctx: EngineContext, title: str, content: str, page_type: str, tags: list[str]
    ) -> Page:
        page_id = str(ulid_lib.ULID())
        page = Page(
            id=page_id,
            title=title,
            content=content,
            type=page_type,
            status="draft",
            tags=tags,
            workspace=ctx.workspace,
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc),
        )
        page.word_count = page.compute_word_count()
        ctx.store.save(page)
        ctx.index.upsert_page(page)
        ctx.output_page_ids.append(page_id)
        return page
