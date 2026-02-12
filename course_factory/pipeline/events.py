"""Pipeline event system for stage lifecycle notifications."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class PipelineEvent:
    """Immutable record of a pipeline lifecycle event."""

    event_type: str
    stage: str
    course_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return (
            f"<PipelineEvent({self.event_type}, stage={self.stage!r}, "
            f"course_id={self.course_id!r})>"
        )


class EventBus:
    """Simple publish-subscribe event bus for pipeline events.

    Supports both synchronous and asynchronous callbacks.
    """

    def __init__(self) -> None:
        self._subscribers: list[Callable[[PipelineEvent], Any]] = []

    def subscribe(self, callback: Callable[[PipelineEvent], Any]) -> None:
        """Register a callback to receive all pipeline events.

        Args:
            callback: Sync or async callable accepting a PipelineEvent.
        """
        self._subscribers.append(callback)
        logger.debug(
            "Subscriber registered: %s (total: %d)",
            getattr(callback, "__name__", repr(callback)),
            len(self._subscribers),
        )

    def emit(self, event: PipelineEvent) -> None:
        """Emit an event to all subscribers synchronously.

        Async callbacks are scheduled but not awaited. Use
        :pymeth:`emit_async` when async callbacks must complete
        before proceeding.

        Args:
            event: The event to broadcast.
        """
        logger.debug("Emitting event: %s", event)
        for callback in self._subscribers:
            try:
                result = callback(event)
                # If the callback returned a coroutine, schedule it
                if asyncio.iscoroutine(result):
                    asyncio.ensure_future(result)
            except Exception:
                logger.exception(
                    "Error in event subscriber %s",
                    getattr(callback, "__name__", repr(callback)),
                )

    async def emit_async(self, event: PipelineEvent) -> None:
        """Emit an event and await all async subscribers.

        Args:
            event: The event to broadcast.
        """
        logger.debug("Emitting async event: %s", event)
        for callback in self._subscribers:
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception(
                    "Error in async event subscriber %s",
                    getattr(callback, "__name__", repr(callback)),
                )
