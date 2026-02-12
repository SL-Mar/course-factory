"""Default configuration template and bootstrap helper."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_YAML: str = """# ============================================================
# Course Factory – configuration file
# ============================================================
# Values here override environment variables (CF_* prefix).
# Uncomment and edit the settings you want to customise.
# ============================================================

# ── Licence ─────────────────────────────────────────────────
# license_key: ""

# ── LLM provider ───────────────────────────────────────────
# ollama_url: "http://localhost:11434"

# ── Database ────────────────────────────────────────────────
# db_url: "postgresql://cf:cf@localhost:5435/course_factory"

# ── Vector store ────────────────────────────────────────────
# qdrant_url: "http://localhost:6333"

# ── Cache / message broker ──────────────────────────────────
# redis_url: "redis://localhost:6379/2"

# ── Cloud API keys (leave blank to disable) ─────────────────
# anthropic_api_key: ""
# openai_api_key: ""

# ── Model selection ─────────────────────────────────────────
# ollama_model: "qwen2.5:14b"
# cloud_provider: "anthropic"
# cloud_model: "claude-sonnet-4-5-20250929"

# ── Notifications ───────────────────────────────────────────
# telegram_webhook: "http://localhost:5678/webhook/send-telegram"

# ── Runtime ─────────────────────────────────────────────────
# log_level: "INFO"
"""


def create_default_config(config_dir: Path) -> Path:
    """Write the default ``config.yaml`` template if it does not exist.

    Parameters
    ----------
    config_dir:
        The directory in which to create the file.

    Returns
    -------
    Path
        Absolute path to the (possibly pre-existing) ``config.yaml``.
    """
    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = config_dir / "config.yaml"

    if yaml_path.exists():
        logger.debug("Config already exists at %s – skipping creation.", yaml_path)
        return yaml_path

    yaml_path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
    logger.info("Created default config at %s", yaml_path)
    return yaml_path
