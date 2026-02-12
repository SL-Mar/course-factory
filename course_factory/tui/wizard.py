"""Onboarding wizard placeholder (Textual TUI, not yet implemented)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class OnboardingWizard:
    """Interactive onboarding wizard for new course projects.

    This will eventually use `textual` to provide a rich terminal UI.
    For now it acts as a stub that directs users to the CLI config
    command.
    """

    def run(self) -> None:
        """Launch the onboarding wizard."""
        logger.info("OnboardingWizard.run() called (placeholder).")
        print(
            "Onboarding wizard not yet implemented. "
            "Use 'cf config init' for now."
        )
