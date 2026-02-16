"""Engine CLI commands."""

from __future__ import annotations

import asyncio

import typer
from rich import print as rprint

engine_app = typer.Typer(help="Engine operations (course, spec, article, docs)")


@engine_app.command("run")
def run_engine(
    engine: str = typer.Argument(..., help="Engine: course, spec, article, docs"),
    topic: str = typer.Option("", help="Topic or brief"),
    workspace: str = typer.Option("default", help="Workspace"),
) -> None:
    """Run an engine pipeline."""
    asyncio.run(_run(engine, topic, workspace))


async def _run(engine_name: str, topic: str, workspace: str) -> None:
    from localnotion.config.settings import Settings
    from localnotion.core.store import PageStore
    from localnotion.core.index import PageIndex
    from localnotion.ai.router import LLMRouter
    from localnotion.engines.base import EngineContext

    settings = Settings.load_yaml()
    store = PageStore(settings.data_dir)
    index = PageIndex(settings.data_dir)
    router = LLMRouter(settings)

    def progress(msg: str) -> None:
        rprint(f"  [dim]{msg}[/dim]")

    ctx = EngineContext(store=store, index=index, router=router, workspace=workspace, progress_cb=progress)

    if engine_name == "course":
        from localnotion.engines.course import CourseEngine
        eng = CourseEngine()
        result = await eng.execute(ctx, topic=topic)
    elif engine_name == "spec":
        from localnotion.engines.spec import SpecEngine
        eng = SpecEngine()
        result = await eng.execute(ctx, brief=topic)
    elif engine_name == "article":
        from localnotion.engines.article import ArticleEngine
        eng = ArticleEngine()
        result = await eng.execute(ctx, topic=topic)
    elif engine_name == "docs":
        from localnotion.engines.docs import DocsEngine
        eng = DocsEngine()
        result = await eng.execute(ctx, product=topic)
    else:
        rprint(f"[red]Unknown engine: {engine_name}[/red]")
        raise typer.Exit(1)

    rprint(f"[green]Engine complete:[/green] {result}")


@engine_app.command("list")
def list_engines() -> None:
    """List available engines."""
    engines = [
        ("course", "Generate courses from knowledge"),
        ("spec", "Generate technical specifications"),
        ("article", "Draft technical articles"),
        ("docs", "Generate product documentation"),
    ]
    for name, desc in engines:
        rprint(f"  [bold]{name}[/bold] — {desc}")
