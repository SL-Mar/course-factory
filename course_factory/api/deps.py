"""FastAPI dependencies."""

from __future__ import annotations

from course_factory.config.settings import Settings
from course_factory.workspace import WorkspaceManager

_ws: WorkspaceManager | None = None
_settings: Settings | None = None


def get_workspace() -> WorkspaceManager:
    """Return a singleton WorkspaceManager."""
    global _ws
    if _ws is None:
        s = get_settings()
        _ws = WorkspaceManager(config_dir=s.config_dir)
    return _ws


def get_settings() -> Settings:
    """Return a singleton Settings (loaded from YAML)."""
    global _settings
    if _settings is None:
        _settings = Settings.load_yaml()
    return _settings


def reset_settings() -> None:
    """Force reload on next access (call after saving config)."""
    global _settings, _ws
    _settings = None
    _ws = None
