"""Slash commands for the page editor."""

from __future__ import annotations

import logging
from typing import Any

from localnotion.ai.router import LLMRouter

logger = logging.getLogger(__name__)


SLASH_COMMANDS = {
    "/ask": "Answer a question using page context + knowledge graph",
    "/summarize": "Summarize the current page",
    "/expand": "Expand the current section with more detail",
    "/translate": "Translate page content to another language",
    "/link": "Suggest related pages to link",
    "/table": "Generate a markdown table from description",
    "/spec": "Invoke the spec engine",
    "/draft": "Invoke the article engine",
    "/tags": "Suggest tags for the current page",
}


async def execute_slash_command(
    command: str,
    page_content: str,
    page_title: str,
    router: LLMRouter,
    extra_context: str = "",
) -> str:
    """Execute a slash command and return the result text."""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/ask":
        messages = [
            {"role": "system", "content": "Answer the question based on the page content provided."},
            {"role": "user", "content": f"Page: {page_title}\n\n{page_content}\n\n{extra_context}\n\nQuestion: {arg}"},
        ]
        result = await router.chat("chat", messages)
        return result.text

    if cmd == "/summarize":
        messages = [
            {"role": "system", "content": "Provide a concise summary of the following page."},
            {"role": "user", "content": f"# {page_title}\n\n{page_content}"},
        ]
        result = await router.chat("summarize", messages)
        return result.text

    if cmd == "/expand":
        messages = [
            {"role": "system", "content": "Expand the following content with more detail, examples, and depth. Return markdown."},
            {"role": "user", "content": f"# {page_title}\n\n{page_content}\n\nExpand on: {arg or 'the entire page'}"},
        ]
        result = await router.chat("expand", messages)
        return result.text

    if cmd == "/translate":
        lang = arg or "French"
        messages = [
            {"role": "system", "content": f"Translate the following content to {lang}. Preserve markdown formatting."},
            {"role": "user", "content": f"# {page_title}\n\n{page_content}"},
        ]
        result = await router.chat("translate", messages)
        return result.text

    if cmd == "/tags":
        messages = [
            {"role": "system", "content": "Suggest 3-8 relevant tags for this page. Return only a JSON array of strings."},
            {"role": "user", "content": f"# {page_title}\n\n{page_content[:3000]}"},
        ]
        result = await router.chat("tag", messages)
        return result.text

    if cmd == "/table":
        messages = [
            {"role": "system", "content": "Generate a markdown table based on the description. Return only the markdown table."},
            {"role": "user", "content": arg or "Generate a table summarizing the key points of this page."},
        ]
        result = await router.chat("chat", messages)
        return result.text

    if cmd == "/link":
        return "Link suggestions require vector search — use the Suggest Links button in the UI."

    if cmd in ("/spec", "/draft"):
        return f"Engine command '{cmd}' should be triggered via the Engines panel."

    return f"Unknown command: {cmd}. Available: {', '.join(SLASH_COMMANDS.keys())}"
