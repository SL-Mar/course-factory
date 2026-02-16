"""AI chat and slash commands API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from localnotion.api.deps import get_llm_router, get_store, get_index, get_vector
from localnotion.api.schemas import ChatRequest, ChatResponse, SlashCommandRequest
from localnotion.ai.agent import Agent
from localnotion.ai.commands import execute_slash_command

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

_agent: Agent | None = None


def _get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent(get_llm_router())
    return _agent


@router.post("/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    agent = _get_agent()

    context_pages = []
    context_ids: list[str] = []

    if req.include_context:
        vector = get_vector()
        search_results = await vector.search(req.message, limit=5)
        store = get_store()
        for sr in search_results:
            try:
                page = store.load(sr.page_id)
                context_pages.append({
                    "id": page.id,
                    "title": page.title,
                    "content": page.content[:2000],
                })
                context_ids.append(page.id)
            except FileNotFoundError:
                pass

    response = await agent.chat(req.message, context_pages=context_pages or None)
    return ChatResponse(response=response, context_pages=context_ids)


@router.post("/reset")
async def reset_chat() -> dict:
    agent = _get_agent()
    agent.reset()
    return {"ok": True}


@router.post("/command")
async def slash_command(req: SlashCommandRequest) -> dict:
    llm_router = get_llm_router()

    # If page_id is provided but no content, load it
    page_content = req.page_content
    page_title = req.page_title
    if req.page_id and not page_content:
        store = get_store()
        try:
            page = store.load(req.page_id)
            page_content = page.content
            page_title = page.title
        except FileNotFoundError:
            pass

    result = await execute_slash_command(
        command=req.command,
        page_content=page_content,
        page_title=page_title,
        router=llm_router,
    )
    return {"result": result}
