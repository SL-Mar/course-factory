"""Abstract base class for pipeline stages."""
from __future__ import annotations

import abc
import logging

logger = logging.getLogger(__name__)


class Stage(abc.ABC):
    """Abstract base for a single pipeline stage.

    Subclasses must implement :pyattr:`name`, :pymeth:`execute`, and
    :pymeth:`validate`.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable identifier for this stage."""

    @abc.abstractmethod
    async def execute(self, context: dict) -> dict:
        """Run the stage logic.

        Args:
            context: Shared pipeline context dict, accumulated from prior stages.

        Returns:
            Updated context dict with this stage's outputs merged in.
        """

    @abc.abstractmethod
    async def validate(self, context: dict) -> bool:
        """Check whether preconditions for this stage are met.

        Args:
            context: Current pipeline context.

        Returns:
            True if the stage can proceed, False otherwise.
        """
