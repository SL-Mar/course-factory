"""Application settings with environment, .env, and YAML layering."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path.home() / "localnotion"
_DEFAULT_CONFIG_DIR = Path.home() / ".config" / "localnotion"


class Settings(BaseSettings):
    """LocalNotion configuration.

    Resolution order (last wins):
      1. Field defaults
      2. ``.env`` file
      3. Environment variables (``LN_`` prefix)
      4. YAML overlay via :meth:`load_yaml`
    """

    model_config = SettingsConfigDict(
        env_prefix="LN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── licence / identity ──────────────────────────────────────────────
    license_key: str = Field(default="", description="LocalNotion licence key (LN- prefix)")

    # ── data directory ──────────────────────────────────────────────────
    data_dir: Path = Field(
        default=_DEFAULT_DATA_DIR,
        description="Root data directory (~/localnotion/)",
    )

    # ── service URLs ────────────────────────────────────────────────────
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant URL")

    # ── API keys ────────────────────────────────────────────────────────
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")

    # ── Model selection ─────────────────────────────────────────────────
    ollama_model: str = Field(default="qwen2.5:14b", description="Local LLM model")
    embed_model: str = Field(default="nomic-embed-text", description="Embedding model")
    cloud_provider: str = Field(default="anthropic", description="Cloud LLM provider")
    cloud_model: str = Field(default="claude-sonnet-4-5-20250929", description="Cloud model")

    # ── integrations ──────────────────────────────────────────────────
    notion_api_key: str = Field(default="", description="Notion API token (for import)")
    github_token: str = Field(default="", description="GitHub PAT")

    # ── notifications ───────────────────────────────────────────────────
    telegram_webhook: str = Field(
        default="http://localhost:5678/webhook/send-telegram",
        description="Telegram webhook URL",
    )

    # ── runtime ─────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO", description="Logging level")
    config_dir: Path = Field(default=_DEFAULT_CONFIG_DIR, description="Config directory")

    # ── YAML layering ───────────────────────────────────────────────────

    @classmethod
    def load_yaml(cls, config_dir: Path | None = None) -> Settings:
        """Create Settings with YAML values merged over env defaults."""
        base = cls()

        if config_dir is None:
            config_dir = base.config_dir

        yaml_path = Path(config_dir) / "config.yaml"
        if not yaml_path.is_file():
            logger.debug("No YAML config at %s", yaml_path)
            return base

        try:
            with open(yaml_path, "r", encoding="utf-8") as fh:
                yaml_data: dict[str, Any] | None = yaml.safe_load(fh)
        except Exception:
            logger.warning("Failed to parse %s", yaml_path, exc_info=True)
            return base

        if not yaml_data:
            return base

        merged = base.model_dump()
        for key, value in yaml_data.items():
            if key in merged and value is not None:
                merged[key] = value

        return cls.model_validate(merged)

    def save_yaml(self, config_dir: Path | None = None) -> Path:
        """Persist settings to config.yaml."""
        target_dir = Path(config_dir) if config_dir else self.config_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = target_dir / "config.yaml"

        data = self.model_dump()
        data["config_dir"] = str(data["config_dir"])
        data["data_dir"] = str(data["data_dir"])

        with open(yaml_path, "w", encoding="utf-8") as fh:
            yaml.dump(data, fh, default_flow_style=False, sort_keys=False)

        logger.info("Settings saved to %s", yaml_path)
        return yaml_path
