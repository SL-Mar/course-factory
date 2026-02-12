"""Stage 3: Research — generate detailed per-module research notes from the outline."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from course_factory.pipeline.stage import Stage

logger = logging.getLogger(__name__)

RESEARCH_PROMPT = """You are a course content researcher. Generate detailed research notes for the following module.

COURSE TITLE: {course_title}

MODULE {module_number}: {module_title}
Description: {module_description}

LESSONS IN THIS MODULE:
{lessons_list}

SOURCE MATERIALS (summaries from knowledge base):
{source_summaries}

Write comprehensive research notes for this module in Markdown format. For EACH lesson, include:

1. **Key Concepts** — core ideas and definitions the lesson must cover
2. **Teaching Points** — specific points to explain, with examples
3. **Code Examples** (if applicable) — short illustrative snippets
4. **References** — which source materials are most relevant
5. **Common Misconceptions** — pitfalls students often encounter

Structure the output as:

# Module {module_number}: {module_title}

## Lesson {lesson_number}: {lesson_title}

### Key Concepts
...

### Teaching Points
...

(repeat for each lesson)

End with a **Module Summary** section that ties all lessons together."""


class ResearchStage(Stage):
    """Generate detailed per-module research notes from the discovery outline."""

    @property
    def name(self) -> str:
        return "research"

    async def validate(self, context: dict) -> bool:
        workspace_dir = context.get("workspace_dir", "")
        if not workspace_dir:
            return False
        outline_path = Path(workspace_dir) / "02-discovery" / "outline.json"
        if not outline_path.is_file():
            return False
        try:
            data = json.loads(outline_path.read_text(encoding="utf-8"))
            return "modules" in data
        except (json.JSONDecodeError, KeyError):
            return False

    async def execute(self, context: dict) -> dict:
        from course_factory.llm.router import LLMRouter

        workspace_dir = Path(context["workspace_dir"])
        outline_path = workspace_dir / "02-discovery" / "outline.json"
        knowledge_dir = workspace_dir / "01-knowledge"
        research_dir = workspace_dir / "03-research"
        research_dir.mkdir(parents=True, exist_ok=True)

        settings = context.get("settings", {})

        # Load outline
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        course_title = outline.get("title", "Untitled Course")
        modules = outline.get("modules", [])

        if not modules:
            raise RuntimeError("Outline contains no modules")

        # Collect source summaries (first ~3000 chars each)
        source_summaries: list[str] = []
        if knowledge_dir.is_dir():
            for md_file in sorted(knowledge_dir.glob("*.md")):
                if md_file.name.startswith("_"):
                    continue
                content = md_file.read_text(encoding="utf-8")[:3000]
                source_summaries.append(f"--- {md_file.stem} ---\n{content}\n")
        combined_sources = "\n".join(source_summaries) if source_summaries else "(no source materials available)"

        # Initialize LLM router
        router = LLMRouter(settings={
            "ollama_base_url": settings.get("ollama_url", "http://localhost:11434"),
        })

        # Build research plan manifest
        research_plan: dict = {
            "course_title": course_title,
            "modules": [],
        }

        # Progress callback (set by workspace_router)
        progress_cb = context.get("_progress_cb")

        for module in modules:
            mod_num = module.get("number", 0)
            mod_title = module.get("title", f"Module {mod_num}")
            mod_desc = module.get("description", "")
            lessons = module.get("lessons", [])

            # Format lessons list
            lessons_list = "\n".join(
                f"  {l.get('number', i+1)}. {l.get('title', 'Untitled')} — {l.get('description', '')}"
                for i, l in enumerate(lessons)
            )

            if progress_cb:
                progress_cb(f"Researching module {mod_num}/{len(modules)}: {mod_title}")

            logger.info("Generating research for module %d: %s", mod_num, mod_title)

            prompt = RESEARCH_PROMPT.format(
                course_title=course_title,
                module_number=mod_num,
                module_title=mod_title,
                module_description=mod_desc,
                lessons_list=lessons_list,
                source_summaries=combined_sources,
                lesson_number="{lesson_number}",
                lesson_title="{lesson_title}",
            )

            research_text = await router.chat(
                task="outline",
                messages=[{"role": "user", "content": prompt}],
            )

            # Save module research file
            slug = _slugify(mod_title)
            filename = f"module-{mod_num:02d}-{slug}.md"
            out_path = research_dir / filename
            out_path.write_text(research_text, encoding="utf-8")
            logger.info("Saved research: %s (%d chars)", filename, len(research_text))

            research_plan["modules"].append({
                "number": mod_num,
                "title": mod_title,
                "file": filename,
                "lessons": len(lessons),
                "status": "done",
            })

        # Save research plan manifest
        plan_path = research_dir / "_research-plan.json"
        plan_path.write_text(json.dumps(research_plan, indent=2), encoding="utf-8")
        logger.info("Saved research plan manifest")

        await router.unload_all()

        context["research_dir"] = str(research_dir)
        return context


def _slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:40].rstrip("-")
