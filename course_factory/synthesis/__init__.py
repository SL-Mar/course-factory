"""Stage 4: Synthesis — transform research notes into structured lesson scripts."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from course_factory.pipeline.stage import Stage

logger = logging.getLogger(__name__)

SCRIPT_PROMPT = """You are an expert course scriptwriter. Write a detailed lesson script for the following lesson.

COURSE: {course_title}
MODULE {module_number}: {module_title}
LESSON {lesson_number}: {lesson_title}
Lesson description: {lesson_description}

RESEARCH NOTES FOR THIS MODULE:
{research_notes}

Write a complete lesson script in Markdown. Structure it as follows:

# Lesson {lesson_number}: {lesson_title}

## Opening Hook
1-2 engaging sentences that draw the learner in and explain why this lesson matters.

## Key Concepts
Define and explain every core concept this lesson covers. Use clear, precise language suitable for the target audience.

## Detailed Walkthrough
Step-by-step teaching narrative. Explain each idea thoroughly as if narrating a video lecture. Use transitions between ideas.

## Examples & Code Demos
Provide concrete examples, code snippets (if applicable), or worked problems that illustrate the concepts.

## Summary & Takeaways
Bullet-point recap of the most important ideas from this lesson.

## Transition
1-2 sentences previewing how this lesson connects to the next topic.

Write in a clear, engaging, instructor-style voice. Be thorough — this script will be used to produce slides and video narration."""


class SynthesisStage(Stage):
    """Transform per-module research notes into per-lesson scripts."""

    @property
    def name(self) -> str:
        return "synthesis"

    async def validate(self, context: dict) -> bool:
        workspace_dir = context.get("workspace_dir", "")
        if not workspace_dir:
            return False
        plan_path = Path(workspace_dir) / "03-research" / "_research-plan.json"
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
        outline_path = workspace_dir / "02-discovery" / "outline.json"
        research_dir = workspace_dir / "03-research"
        synthesis_dir = workspace_dir / "04-synthesis"
        synthesis_dir.mkdir(parents=True, exist_ok=True)

        settings = context.get("settings", {})

        # Load outline for lesson metadata
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        course_title = outline.get("title", "Untitled Course")
        modules = outline.get("modules", [])

        if not modules:
            raise RuntimeError("Outline contains no modules")

        # Load research plan for file mapping
        research_plan = json.loads(
            (research_dir / "_research-plan.json").read_text(encoding="utf-8")
        )
        research_file_map: dict[int, str] = {}
        for mod in research_plan.get("modules", []):
            research_file_map[mod["number"]] = mod["file"]

        # Initialize LLM router
        router = LLMRouter(settings={
            "ollama_base_url": settings.get("ollama_url", "http://localhost:11434"),
            "ollama_model": settings.get("ollama_model", ""),
            "cloud_provider": settings.get("cloud_provider", ""),
            "cloud_model": settings.get("cloud_model", ""),
            "anthropic_api_key": settings.get("anthropic_api_key", ""),
            "openai_api_key": settings.get("openai_api_key", ""),
        })

        token_summary = StageTokenSummary("synthesis")

        # Build synthesis plan manifest
        synthesis_plan: dict = {
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

            # Read research notes for this module
            research_filename = research_file_map.get(mod_num)
            if research_filename:
                research_path = research_dir / research_filename
                research_notes = research_path.read_text(encoding="utf-8") if research_path.is_file() else "(no research notes available)"
            else:
                research_notes = "(no research notes available)"

            # Create module output directory
            mod_dir = synthesis_dir / f"module-{mod_num:02d}"
            mod_dir.mkdir(parents=True, exist_ok=True)

            module_plan_entry: dict = {
                "number": mod_num,
                "title": mod_title,
                "lessons": [],
            }

            for lesson in lessons:
                lesson_num = lesson.get("number", 0)
                lesson_title = lesson.get("title", f"Lesson {lesson_num}")
                lesson_desc = lesson.get("description", "")

                lesson_counter += 1
                if progress_cb:
                    progress_cb(
                        f"Writing script {lesson_counter}/{total_lessons}: "
                        f"Module {mod_num} — {lesson_title}"
                    )

                logger.info(
                    "Generating script for module %d, lesson %d: %s",
                    mod_num, lesson_num, lesson_title,
                )

                prompt = SCRIPT_PROMPT.format(
                    course_title=course_title,
                    module_number=mod_num,
                    module_title=mod_title,
                    lesson_number=lesson_num,
                    lesson_title=lesson_title,
                    lesson_description=lesson_desc,
                    research_notes=research_notes,
                )

                result = await router.chat(
                    task="script_writing",
                    messages=[{"role": "user", "content": prompt}],
                )
                token_summary.add_call(result)

                # Save lesson script
                slug = _slugify(lesson_title)
                filename = f"lesson-{lesson_num:02d}-{slug}.md"
                out_path = mod_dir / filename
                out_path.write_text(result.text, encoding="utf-8")
                logger.info(
                    "Saved script: module-%02d/%s (%d chars)",
                    mod_num, filename, len(result.text),
                )

                module_plan_entry["lessons"].append({
                    "number": lesson_num,
                    "title": lesson_title,
                    "file": f"module-{mod_num:02d}/{filename}",
                    "status": "done",
                })

            synthesis_plan["modules"].append(module_plan_entry)

        # Save synthesis plan manifest
        plan_path = synthesis_dir / "_synthesis-plan.json"
        plan_path.write_text(json.dumps(synthesis_plan, indent=2), encoding="utf-8")
        logger.info("Saved synthesis plan manifest")

        save_token_usage(workspace_dir, "synthesis", token_summary)
        context["_tokens_synthesis"] = token_summary.to_dict()

        await router.unload_all()

        context["synthesis_dir"] = str(synthesis_dir)
        return context


def _slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:40].rstrip("-")
