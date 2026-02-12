"""Application settings with environment, .env, and YAML layering."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_DIR = Path.home() / ".config" / "course-factory"


class Settings(BaseSettings):
    """Course Factory configuration.

    Resolution order (last wins):
      1. Field defaults (below)
      2. ``.env`` file
      3. Real environment variables (``CF_`` prefix)
      4. YAML overlay via :meth:`load_yaml`
    """

    model_config = SettingsConfigDict(
        env_prefix="CF_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── licence / identity ──────────────────────────────────────────────
    license_key: str = Field(default="", description="Course Factory licence key")

    # ── service URLs ────────────────────────────────────────────────────
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL",
    )
    db_url: str = Field(
        default="postgresql://cf:cf@localhost:5435/course_factory",
        description="PostgreSQL connection string",
    )
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant vector-store URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/2",
        description="Redis connection string",
    )

    # ── API keys ────────────────────────────────────────────────────────
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")

    # ── notifications ───────────────────────────────────────────────────
    telegram_webhook: str = Field(
        default="http://localhost:5678/webhook/send-telegram",
        description="Telegram notification webhook URL",
    )

    # ── runtime ─────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO", description="Logging level")
    config_dir: Path = Field(
        default=_DEFAULT_CONFIG_DIR,
        description="Directory for persistent configuration files",
    )

    # ── YAML layering ───────────────────────────────────────────────────

    @classmethod
    def load_yaml(cls, config_dir: Path | None = None) -> "Settings":
        """Create a *Settings* instance with YAML values merged over env defaults.

        Parameters
        ----------
        config_dir:
            Override the directory that contains ``config.yaml``.
            Falls back to the ``CF_CONFIG_DIR`` env var, then the
            built-in default (``~/.config/course-factory``).

        Returns
        -------
        Settings
            Fully-resolved settings object.
        """
        # Start with env / .env resolved values.
        base = cls()

        if config_dir is None:
            config_dir = base.config_dir

        yaml_path = Path(config_dir) / "config.yaml"
        if not yaml_path.is_file():
            logger.debug("No YAML config at %s – using env defaults only.", yaml_path)
            return base

        try:
            with open(yaml_path, "r", encoding="utf-8") as fh:
                yaml_data: dict[str, Any] | None = yaml.safe_load(fh)
        except Exception:
            logger.warning("Failed to parse %s – falling back to env defaults.", yaml_path, exc_info=True)
            return base

        if not yaml_data:
            return base

        # Merge: YAML values override env defaults for any key present.
        merged = base.model_dump()
        for key, value in yaml_data.items():
            if key in merged and value is not None:
                merged[key] = value

        return cls.model_validate(merged)

    def save_yaml(self, config_dir: Path | None = None) -> Path:
        """Persist the current settings to ``config.yaml``.

        Parameters
        ----------
        config_dir:
            Target directory.  Defaults to ``self.config_dir``.

        Returns
        -------
        Path
            The path to the written YAML file.
        """
        target_dir = Path(config_dir) if config_dir else self.config_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = target_dir / "config.yaml"

        # Serialise with Path objects converted to strings.
        data = self.model_dump()
        data["config_dir"] = str(data["config_dir"])

        with open(yaml_path, "w", encoding="utf-8") as fh:
            yaml.dump(data, fh, default_flow_style=False, sort_keys=False)

        logger.info("Settings saved to %s", yaml_path)
        return yaml_path
