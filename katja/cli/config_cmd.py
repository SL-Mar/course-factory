"""Configuration management commands."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from katja.config.settings import Settings

console = Console()
config_app = typer.Typer(name="config", help="Configuration management")

_SECRET_FIELDS = {"anthropic_api_key", "openai_api_key", "license_key", "notion_api_key"}


def _mask(value: str) -> str:
    if not value:
        return "(not set)"
    if len(value) <= 4:
        return "****"
    return "*" * (len(value) - 4) + value[-4:]


@config_app.command()
def init() -> None:
    """Create the default configuration directory and YAML file."""
    settings = Settings()
    yaml_path = settings.save_yaml()
    console.print(Panel.fit(
        f"[green]Configuration initialised[/green]\n\n"
        f"  Config dir:  [bold]{settings.config_dir}[/bold]\n"
        f"  Config file: [bold]{yaml_path}[/bold]",
        title="Config",
    ))


@config_app.command()
def show() -> None:
    """Display current settings (secrets masked)."""
    settings = Settings.load_yaml()
    data = settings.model_dump()

    for key, value in data.items():
        if isinstance(value, Path):
            data[key] = str(value)

    for field_name in _SECRET_FIELDS:
        if field_name in data:
            data[field_name] = _mask(str(data[field_name]))

    formatted = yaml.dump(data, default_flow_style=False, sort_keys=False)
    console.print(Panel(
        f"[cyan]{formatted}[/cyan]",
        title="[bold]Current Settings[/bold]",
        subtitle=f"[dim]{settings.config_dir / 'config.yaml'}[/dim]",
    ))
