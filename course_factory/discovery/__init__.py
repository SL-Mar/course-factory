"""Stage 1: Discovery — LLM-powered course proposal and outline generation."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from course_factory.pipeline.stage import Stage

logger = logging.getLogger(__name__)

PROPOSAL_PROMPT = """You are a course design expert. Based on the following source materials, create a detailed course proposal.

SOURCE MATERIALS:
{sources}

Create a comprehensive course proposal in Markdown format with:
1. Course title
2. Target audience
3. Learning objectives (5-8 bullet points)
4. Prerequisites
5. Course modules (4-8 modules), each with:
   - Module title
   - Brief description
   - 3-5 lessons per module
6. Estimated duration
7. Assessment strategy

Write the proposal as a professional document ready for review."""

OUTLINE_PROMPT = """Extract a structured JSON course outline from the following course proposal.

PROPOSAL:
{proposal}

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "title": "Course Title",
  "modules": [
    {{
      "number": 1,
      "title": "Module Title",
      "description": "Brief description",
      "lessons": [
        {{
          "number": 1,
          "title": "Lesson Title",
          "description": "Brief description"
        }}
      ]
    }}
  ]
}}"""


class DiscoveryStage(Stage):
    """Generate a course proposal and structured outline from knowledge sources."""

    @property
    def name(self) -> str:
        return "discovery"

    async def validate(self, context: dict) -> bool:
        workspace_dir = context.get("workspace_dir", "")
        knowledge_dir = Path(workspace_dir) / "01-knowledge" if workspace_dir else None
        if not knowledge_dir or not knowledge_dir.is_dir():
            return False
        # Need at least one .md file
        return any(knowledge_dir.glob("*.md"))

    async def execute(self, context: dict) -> dict:
        from course_factory.llm.router import LLMRouter

        workspace_dir = Path(context["workspace_dir"])
        knowledge_dir = workspace_dir / "01-knowledge"
        discovery_dir = workspace_dir / "02-discovery"
        discovery_dir.mkdir(parents=True, exist_ok=True)

        settings = context.get("settings", {})

        # Collect source content (first ~2000 chars per source)
        source_summaries: list[str] = []
        for md_file in sorted(knowledge_dir.glob("*.md")):
            if md_file.name.startswith("_"):
                continue
            content = md_file.read_text(encoding="utf-8")[:2000]
            source_summaries.append(f"--- {md_file.stem} ---\n{content}\n")

        if not source_summaries:
            raise RuntimeError("No knowledge sources found in 01-knowledge/")

        combined_sources = "\n".join(source_summaries)

        # Initialize LLM router
        router = LLMRouter(settings={
            "ollama_base_url": settings.get("ollama_url", "http://localhost:11434"),
        })

        # Step 1: Generate course proposal
        logger.info("Generating course proposal via LLM...")
        proposal = await router.chat(
            task="outline",
            messages=[
                {"role": "user", "content": PROPOSAL_PROMPT.format(sources=combined_sources)}
            ],
        )

        proposal_path = discovery_dir / "course-proposal.md"
        proposal_path.write_text(proposal, encoding="utf-8")
        logger.info("Saved course proposal (%d chars)", len(proposal))

        # Step 2: Extract structured outline
        logger.info("Extracting structured outline via LLM...")
        outline_raw = await router.chat(
            task="outline",
            messages=[
                {"role": "user", "content": OUTLINE_PROMPT.format(proposal=proposal)}
            ],
        )

        # Try to parse JSON from the response
        outline_json = _extract_json(outline_raw)
        outline_path = discovery_dir / "outline.json"
        outline_path.write_text(
            json.dumps(outline_json, indent=2), encoding="utf-8"
        )
        logger.info("Saved structured outline")

        await router.unload_all()

        context["course_proposal"] = str(proposal_path)
        context["course_outline"] = str(outline_path)
        return context


def _extract_json(text: str) -> dict:
    """Best-effort JSON extraction from LLM output."""
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in markdown
    import re
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    # Fallback: save raw text as error
    return {"error": "Could not parse outline", "raw": text[:2000]}
