"""Base engine class for all agentic pipelines."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import ulid as ulid_lib

from localnotion.ai.router import LLMRouter
from localnotion.core.index import PageIndex
from localnotion.core.store import PageStore

logger = logging.getLogger(__name__)


class EngineContext:
    """Shared context passed through engine stages."""

    def __init__(
        self,
        store: PageStore,
        index: PageIndex,
        router: LLMRouter,
        workspace: str = "default",
        progress_cb: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.store = store
        self.index = index
        self.router = router
        self.workspace = workspace
        self.progress_cb = progress_cb
        self.data: dict[str, Any] = {}
        self.output_page_ids: list[str] = []
        self.tokens_used: int = 0
        self.cost_usd: float = 0.0

    def report(self, message: str) -> None:
        logger.info(message)
        if self.progress_cb:
            self.progress_cb(message)


class Engine(ABC):
    """Abstract base for all LocalNotion engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Engine identifier (e.g. 'course', 'spec', 'article', 'docs')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable engine name."""
        ...

    @abstractmethod
    async def execute(self, ctx: EngineContext, **kwargs: Any) -> dict[str, Any]:
        """Run the engine pipeline. Returns a result dict."""
        ...

    def create_run_record(self, ctx: EngineContext, status: str = "running", error: str = "") -> dict[str, Any]:
        """Create an engine run record for the index."""
        return {
            "run_id": str(ulid_lib.ULID()),
            "engine": self.name,
            "status": status,
            "input_pages": list(ctx.data.get("input_page_ids", [])),
            "output_pages": ctx.output_page_ids,
            "llm_model": "",
            "tokens_used": ctx.tokens_used,
            "cost_usd": ctx.cost_usd,
            "started_at": ctx.data.get("started_at", datetime.now(timezone.utc).isoformat()),
            "completed_at": datetime.now(timezone.utc).isoformat() if status != "running" else "",
            "error": error,
        }
