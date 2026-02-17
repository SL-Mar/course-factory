"""AI agent with tool-using capabilities for Katja operations."""

from __future__ import annotations

import json
import logging
from typing import Any

from katja.ai.router import LLMRouter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Katja AI, a knowledge management assistant.
You help users organize, search, create, and transform their knowledge.

You have access to the user's knowledge base including:
- Pages (markdown documents with wiki-links)
- Tables (structured data)
- A knowledge graph connecting all content

When answering questions:
- Search the knowledge base for relevant content
- Cite specific pages using [[page-title]] notation
- Be concise and actionable
- If you don't know something, say so honestly

You can help with:
- Finding information across pages
- Summarizing content
- Suggesting connections between ideas
- Drafting new content based on existing knowledge
- Running engines (course, spec, article, docs generation)
"""


class Agent:
    """Tool-using AI agent for Katja."""

    def __init__(self, router: LLMRouter) -> None:
        self.router = router
        self.conversation: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    async def chat(
        self,
        user_message: str,
        context_pages: list[dict[str, str]] | None = None,
    ) -> str:
        """Process a user message and return AI response.

        Optionally include relevant page content as context.
        """
        # Build context from relevant pages
        if context_pages:
            ctx = "\n\n---\n\n".join(
                f"**{p['title']}** (ID: {p['id']})\n{p['content'][:2000]}"
                for p in context_pages
            )
            enriched = f"Relevant knowledge base context:\n\n{ctx}\n\n---\n\nUser: {user_message}"
        else:
            enriched = user_message

        self.conversation.append({"role": "user", "content": enriched})

        result = await self.router.chat("chat", self.conversation)

        self.conversation.append({"role": "assistant", "content": result.text})

        # Keep conversation manageable (last 20 messages + system)
        if len(self.conversation) > 21:
            self.conversation = [self.conversation[0]] + self.conversation[-20:]

        return result.text

    def reset(self) -> None:
        """Clear conversation history."""
        self.conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
