"""Pipeline engine that orchestrates multi-stage course generation."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from course_factory.pipeline.events import EventBus, PipelineEvent
from course_factory.pipeline.stage import Stage

logger = logging.getLogger(__name__)

_DEFAULT_CHECKPOINT_DIR = Path.home() / ".config" / "course-factory" / "checkpoints"


class PipelineEngine:
    """Sequentially execute pipeline stages with checkpointing and events.

    Args:
        stages: Ordered list of Stage instances to execute.
        checkpoint_dir: Directory to persist checkpoint files.
            Defaults to ``~/.config/course-factory/checkpoints/``.
    """

    def __init__(
        self,
        stages: list[Stage],
        checkpoint_dir: Path | None = None,
    ) -> None:
        self.stages = stages
        self.checkpoint_dir = checkpoint_dir or _DEFAULT_CHECKPOINT_DIR
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.event_bus = EventBus()

    # ------------------------------------------------------------------
    # Public callbacks (convenience wrappers around EventBus)
    # ------------------------------------------------------------------

    def on_stage_start(self, callback: Any) -> None:
        """Register a callback fired when a stage begins."""
        self.event_bus.subscribe(
            lambda e, cb=callback: cb(e) if e.event_type == "stage_start" else None
        )

    def on_stage_complete(self, callback: Any) -> None:
        """Register a callback fired when a stage completes."""
        self.event_bus.subscribe(
            lambda e, cb=callback: cb(e) if e.event_type == "stage_complete" else None
        )

    def on_error(self, callback: Any) -> None:
        """Register a callback fired when a stage errors."""
        self.event_bus.subscribe(
            lambda e, cb=callback: cb(e) if e.event_type == "stage_error" else None
        )

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    async def run(self, course_id: str, context: dict | None = None) -> dict:
        """Execute all stages sequentially for a given course.

        If a checkpoint exists for *course_id*, the pipeline resumes from
        the stage **after** the last successfully checkpointed one.

        Args:
            course_id: Unique identifier for the course being generated.
            context: Initial context dict; merged with checkpoint data if
                resuming.

        Returns:
            Final context dict after all stages complete.

        Raises:
            RuntimeError: If a stage fails validation or execution.
        """
        context = dict(context or {})
        start_index = 0

        # Attempt to resume from checkpoint
        checkpoint = self.load_checkpoint(course_id)
        if checkpoint is not None:
            last_stage_name, saved_context = checkpoint
            context.update(saved_context)
            # Find the index of the stage *after* the checkpointed one
            for idx, stage in enumerate(self.stages):
                if stage.name == last_stage_name:
                    start_index = idx + 1
                    break
            logger.info(
                "Resuming pipeline for course %s from stage index %d (after %r)",
                course_id,
                start_index,
                last_stage_name,
            )

        for stage in self.stages[start_index:]:
            logger.info(
                "Pipeline [%s] starting stage: %s", course_id, stage.name
            )

            # Emit start event
            await self.event_bus.emit_async(
                PipelineEvent(
                    event_type="stage_start",
                    stage=stage.name,
                    course_id=course_id,
                )
            )

            # Validate preconditions
            try:
                is_valid = await stage.validate(context)
            except Exception as exc:
                await self._handle_error(course_id, stage.name, exc)
                raise RuntimeError(
                    f"Validation failed for stage {stage.name!r}: {exc}"
                ) from exc

            if not is_valid:
                err = RuntimeError(
                    f"Preconditions not met for stage {stage.name!r}"
                )
                await self._handle_error(course_id, stage.name, err)
                raise err

            # Execute stage
            try:
                context = await stage.execute(context)
            except Exception as exc:
                await self._handle_error(course_id, stage.name, exc)
                raise RuntimeError(
                    f"Stage {stage.name!r} failed: {exc}"
                ) from exc

            # Persist checkpoint
            self.save_checkpoint(course_id, stage.name, context)

            # Emit completion event
            await self.event_bus.emit_async(
                PipelineEvent(
                    event_type="stage_complete",
                    stage=stage.name,
                    course_id=course_id,
                    data={"context_keys": list(context.keys())},
                )
            )

            logger.info(
                "Pipeline [%s] completed stage: %s", course_id, stage.name
            )

        return context

    # ------------------------------------------------------------------
    # Checkpointing
    # ------------------------------------------------------------------

    def save_checkpoint(
        self, course_id: str, stage_name: str, context: dict
    ) -> None:
        """Persist pipeline state to disk after a stage completes.

        Args:
            course_id: Course identifier.
            stage_name: Name of the stage that just completed.
            context: Current pipeline context to serialize.
        """
        checkpoint_path = self._checkpoint_path(course_id)
        payload = {
            "course_id": course_id,
            "stage": stage_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": self._serialize_context(context),
        }
        checkpoint_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.debug(
            "Checkpoint saved: course=%s stage=%s path=%s",
            course_id,
            stage_name,
            checkpoint_path,
        )

    def load_checkpoint(self, course_id: str) -> tuple[str, dict] | None:
        """Load the latest checkpoint for a course.

        Args:
            course_id: Course identifier.

        Returns:
            Tuple of (last_stage_name, context) or None if no checkpoint
            exists.
        """
        checkpoint_path = self._checkpoint_path(course_id)
        if not checkpoint_path.exists():
            return None

        try:
            payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            logger.info(
                "Loaded checkpoint for course %s at stage %r",
                course_id,
                payload["stage"],
            )
            return payload["stage"], payload["context"]
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning(
                "Corrupt checkpoint for course %s, ignoring: %s",
                course_id,
                exc,
            )
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _checkpoint_path(self, course_id: str) -> Path:
        """Return the filesystem path for a course checkpoint."""
        safe_id = course_id.replace("/", "_").replace("\\", "_")
        return self.checkpoint_dir / f"{safe_id}.json"

    async def _handle_error(
        self, course_id: str, stage_name: str, exc: Exception
    ) -> None:
        """Emit an error event."""
        logger.error(
            "Pipeline [%s] error in stage %s: %s",
            course_id,
            stage_name,
            exc,
        )
        await self.event_bus.emit_async(
            PipelineEvent(
                event_type="stage_error",
                stage=stage_name,
                course_id=course_id,
                data={"error": str(exc), "error_type": type(exc).__name__},
            )
        )

    @staticmethod
    def _serialize_context(context: dict) -> dict:
        """Best-effort JSON-safe serialization of the context dict.

        Non-serializable values are converted to their string repr.
        """
        safe: dict[str, Any] = {}
        for key, value in context.items():
            try:
                json.dumps(value)
                safe[key] = value
            except (TypeError, ValueError):
                safe[key] = repr(value)
        return safe
