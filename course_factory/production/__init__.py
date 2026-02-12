"""Stage 5: Production — transform lesson scripts into Marp slide decks."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from course_factory.pipeline.stage import Stage

logger = logging.getLogger(__name__)

SLIDE_PROMPT = """You are an expert instructional designer. Convert the following lesson script into a Marp-compatible slide deck.

COURSE: {course_title}
MODULE {module_number}: {module_title}
LESSON {lesson_number}: {lesson_title}

LESSON SCRIPT:
{lesson_script}

Generate a Marp markdown slide deck following these rules:

1. Start with YAML frontmatter:
---
marp: true
theme: default
paginate: true
header: "Module {module_number}: {module_title}"
footer: "{course_title}"
---

2. Use `---` to separate slides.

3. Map the script sections to slides:
   - Opening Hook → 1 title slide with lesson title as H1 and hook text
   - Key Concepts → 1-3 concept slides (H2 heading per slide)
   - Detailed Walkthrough → 2-5 slides breaking down the explanation
   - Examples & Code Demos → 1-3 slides with code blocks isolated on their own slides
   - Summary & Takeaways → 1 recap slide with bullet points
   - Transition → 1 closing slide previewing the next topic

4. Formatting rules:
   - Maximum 6 bullet points per slide
   - Code blocks must be on their own dedicated slide
   - Use H1 (#) only for the title slide, H2 (##) for all other slide headings
   - Add `<!-- speaker notes -->` HTML comments below slide content for narration guidance

5. Target 10-20 slides total for this lesson.

6. Output ONLY the raw Marp markdown. Do NOT wrap it in ```markdown fences."""


class ProductionStage(Stage):
    """Transform per-lesson scripts into Marp slide decks."""

    @property
    def name(self) -> str:
        return "production"

    async def validate(self, context: dict) -> bool:
        workspace_dir = context.get("workspace_dir", "")
        if not workspace_dir:
            return False
        plan_path = Path(workspace_dir) / "04-synthesis" / "_synthesis-plan.json"
        if not plan_path.is_file():
            return False
        try:
            data = json.loads(plan_path.read_text(encoding="utf-8"))
            return "modules" in data
        except (json.JSONDecodeError, KeyError):
            return False

    async def execute(self, context: dict) -> dict:
        from course_factory.llm.router import LLMRouter
        from course_factory.llm.types import StageTokenSummary, save_token_usage

        workspace_dir = Path(context["workspace_dir"])
        synthesis_dir = workspace_dir / "04-synthesis"
        production_dir = workspace_dir / "05-production"
        production_dir.mkdir(parents=True, exist_ok=True)

        settings = context.get("settings", {})

        # Load synthesis plan for file mapping + course metadata
        synthesis_plan = json.loads(
            (synthesis_dir / "_synthesis-plan.json").read_text(encoding="utf-8")
        )
        course_title = synthesis_plan.get("course_title", "Untitled Course")
        modules = synthesis_plan.get("modules", [])

        if not modules:
            raise RuntimeError("Synthesis plan contains no modules")

        # Initialize LLM router
        router = LLMRouter(settings={
            "ollama_base_url": settings.get("ollama_url", "http://localhost:11434"),
            "ollama_model": settings.get("ollama_model", ""),
            "cloud_provider": settings.get("cloud_provider", ""),
            "cloud_model": settings.get("cloud_model", ""),
            "anthropic_api_key": settings.get("anthropic_api_key", ""),
            "openai_api_key": settings.get("openai_api_key", ""),
        })

        token_summary = StageTokenSummary("production")

        # Build production plan manifest
        production_plan: dict = {
            "course_title": course_title,
            "modules": [],
        }

        progress_cb = context.get("_progress_cb")

        total_lessons = sum(len(m.get("lessons", [])) for m in modules)
        lesson_counter = 0

        for module in modules:
            mod_num = module.get("number", 0)
            mod_title = module.get("title", f"Module {mod_num}")
            lessons = module.get("lessons", [])

            # Create module output directory
            mod_dir = production_dir / f"module-{mod_num:02d}"
            mod_dir.mkdir(parents=True, exist_ok=True)

            module_plan_entry: dict = {
                "number": mod_num,
                "title": mod_title,
                "lessons": [],
            }

            for lesson in lessons:
                lesson_num = lesson.get("number", 0)
                lesson_title = lesson.get("title", f"Lesson {lesson_num}")
                source_file = lesson.get("file", "")

                lesson_counter += 1
                if progress_cb:
                    progress_cb(
                        f"Generating slides {lesson_counter}/{total_lessons}: "
                        f"Module {mod_num} — {lesson_title}"
                    )

                logger.info(
                    "Generating slides for module %d, lesson %d: %s",
                    mod_num, lesson_num, lesson_title,
                )

                # Read lesson script from synthesis output
                script_path = synthesis_dir / source_file
                if script_path.is_file():
                    lesson_script = script_path.read_text(encoding="utf-8")
                else:
                    logger.warning("Script not found: %s, skipping", script_path)
                    lesson_script = "(script not available)"

                prompt = SLIDE_PROMPT.format(
                    course_title=course_title,
                    module_number=mod_num,
                    module_title=mod_title,
                    lesson_number=lesson_num,
                    lesson_title=lesson_title,
                    lesson_script=lesson_script,
                )

                result = await router.chat(
                    task="slide_generation",
                    messages=[{"role": "user", "content": prompt}],
                )
                token_summary.add_call(result)

                # Defensive cleanup — strip wrapping markdown fences
                slide_content = _strip_markdown_fences(result.text)

                # Save slide deck
                slug = _slugify(lesson_title)
                filename = f"lesson-{lesson_num:02d}-{slug}.marp.md"
                out_path = mod_dir / filename
                out_path.write_text(slide_content, encoding="utf-8")
                logger.info(
                    "Saved slides: module-%02d/%s (%d chars)",
                    mod_num, filename, len(slide_content),
                )

                module_plan_entry["lessons"].append({
                    "number": lesson_num,
                    "title": lesson_title,
                    "file": f"module-{mod_num:02d}/{filename}",
                    "source_script": source_file,
                    "status": "done",
                })

            production_plan["modules"].append(module_plan_entry)

        # Save production plan manifest
        plan_path = production_dir / "_production-plan.json"
        plan_path.write_text(json.dumps(production_plan, indent=2), encoding="utf-8")
        logger.info("Saved production plan manifest")

        save_token_usage(workspace_dir, "production", token_summary)
        context["_tokens_production"] = token_summary.to_dict()

        await router.unload_all()

        context["production_dir"] = str(production_dir)
        return context


def _strip_markdown_fences(text: str) -> str:
    """Remove wrapping ```markdown fences if the LLM adds them despite instructions."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # Remove opening fence (```markdown, ```md, or just ```)
        stripped = re.sub(r"^```[a-zA-Z]*\n?", "", stripped, count=1)
        # Remove closing fence
        stripped = re.sub(r"\n?```\s*$", "", stripped)
    return stripped.strip()


def _slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:40].rstrip("-")
