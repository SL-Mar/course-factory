"""Import CLI commands."""

from __future__ import annotations

import asyncio

import typer
from rich import print as rprint

import_app = typer.Typer(help="Import from Notion, Obsidian, or markdown")


@import_app.command("notion")
def import_notion(
    token: str = typer.Argument(..., help="Notion API token"),
    workspace: str = typer.Option("notion-import", help="Target workspace"),
) -> None:
    """Import a Notion workspace."""
    asyncio.run(_import_notion(token, workspace))


async def _import_notion(token: str, workspace: str) -> None:
    from katja.config.settings import Settings
    from katja.core.store import PageStore
    from katja.core.index import PageIndex
    from katja.importers.notion import NotionImporter

    settings = Settings.load_yaml()
    store = PageStore(settings.data_dir)
    index = PageIndex(settings.data_dir)
    importer = NotionImporter(token=token, store=store, index=index)

    rprint("[bold]Importing from Notion...[/bold]")
    stats = await importer.import_workspace(workspace=workspace)
    rprint(f"[green]Done:[/green] {stats}")


@import_app.command("markdown")
def import_markdown(
    source_dir: str = typer.Argument(..., help="Path to markdown directory"),
    workspace: str = typer.Option("imported", help="Target workspace"),
    recursive: bool = typer.Option(True, help="Recurse into subdirectories"),
) -> None:
    """Import a directory of markdown files."""
    from katja.config.settings import Settings
    from katja.core.store import PageStore
    from katja.core.index import PageIndex
    from katja.importers.markdown import MarkdownImporter

    settings = Settings.load_yaml()
    store = PageStore(settings.data_dir)
    index = PageIndex(settings.data_dir)
    importer = MarkdownImporter(store, index)

    rprint(f"[bold]Importing from {source_dir}...[/bold]")
    stats = importer.import_directory(source_dir, workspace=workspace, recursive=recursive)
    rprint(f"[green]Done:[/green] {stats}")
