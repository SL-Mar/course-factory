"""Configuration management commands."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from course_factory.config.defaults import create_default_config
from course_factory.config.settings import Settings

console = Console()
config_app = typer.Typer(name="config", help="Configuration management")

# Keys whose values should be masked in display output
_SECRET_FIELDS = {"anthropic_api_key", "openai_api_key", "license_key"}


def _mask(value: str) -> str:
    """Mask a secret value, showing only the last 4 characters."""
    if not value:
        return "(not set)"
    if len(value) <= 4:
        return "****"
    return "*" * (len(value) - 4) + value[-4:]


@config_app.command()
def init() -> None:
    """Create the default configuration directory and YAML file."""
    settings = Settings()
    config_dir = settings.config_dir

    try:
        yaml_path = create_default_config(config_dir)
    except Exception as exc:
        console.print(f"[red]Failed to create config: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print(Panel.fit(
        f"[green]Configuration initialised[/green]\n\n"
        f"  Config dir:  [bold]{config_dir}[/bold]\n"
        f"  Config file: [bold]{yaml_path}[/bold]\n\n"
        f"[dim]Edit the YAML file to customise your settings.[/dim]",
        title="Config",
    ))


@config_app.command()
def show() -> None:
    """Display current settings (API keys are masked)."""
    try:
        settings = Settings.load_yaml()
    except Exception as exc:
        console.print(f"[red]Failed to load settings: {exc}[/red]")
        raise typer.Exit(code=1)

    data = settings.model_dump()

    # Convert Path objects to strings for YAML serialisation
    for key, value in data.items():
        if isinstance(value, Path):
            data[key] = str(value)

    # Mask secret fields
    for field_name in _SECRET_FIELDS:
        if field_name in data:
            data[field_name] = _mask(str(data[field_name]))

    formatted = yaml.dump(data, default_flow_style=False, sort_keys=False)

    console.print(Panel(
        f"[cyan]{formatted}[/cyan]",
        title="[bold]Current Settings[/bold]",
        subtitle=f"[dim]{settings.config_dir / 'config.yaml'}[/dim]",
    ))
