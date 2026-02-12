"""Main Typer application and sub-command registration."""

from __future__ import annotations

import typer
from rich import print as rprint

import course_factory
from course_factory.cli.keygen_cmd import keygen_app
from course_factory.cli.config_cmd import config_app
from course_factory.cli.pipeline_cmd import pipeline_app

app = typer.Typer(
    name="cf",
    help="Course Factory - Transform knowledge into courses",
    add_completion=False,
)

# ── sub-command groups ──────────────────────────────────────────────────
app.add_typer(keygen_app, name="keygen")
app.add_typer(config_app, name="config")
app.add_typer(pipeline_app, name="pipeline")


# ── top-level commands ──────────────────────────────────────────────────


@app.command()
def version() -> None:
    """Print the Course Factory version."""
    rprint(f"[bold cyan]Course Factory[/bold cyan] v{course_factory.__version__}")


@app.command()
def ingest() -> None:
    """Ingest knowledge sources (PDF, video, repo)."""
    rprint("[yellow]Not yet implemented[/yellow]")


# ── entry point wrapper ─────────────────────────────────────────────────


def app_main() -> None:
    """Entry point for the ``cf`` console script."""
    app()
