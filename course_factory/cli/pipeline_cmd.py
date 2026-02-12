"""Course generation pipeline commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

console = Console()
pipeline_app = typer.Typer(name="pipeline", help="Course generation pipeline")


@pipeline_app.command()
def run(
    course_id: Optional[str] = typer.Argument(None, help="Course identifier to process"),
) -> None:
    """Run the course generation pipeline."""
    if course_id:
        console.print(
            f"[yellow]Pipeline not yet implemented. "
            f"Use 'cf pipeline run {course_id}' when stages are ready.[/yellow]"
        )
    else:
        console.print(
            "[yellow]Pipeline not yet implemented. "
            "Use 'cf pipeline run <course_id>' when stages are ready.[/yellow]"
        )


@pipeline_app.command()
def status(
    course_id: str = typer.Argument(..., help="Course identifier to check"),
) -> None:
    """Check the status of a pipeline run."""
    console.print("[yellow]Pipeline status not yet implemented.[/yellow]")
