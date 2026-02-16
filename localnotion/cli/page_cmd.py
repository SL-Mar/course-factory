"""Page management CLI commands."""

from __future__ import annotations

from datetime import datetime, timezone

import typer
from rich import print as rprint
from rich.table import Table

import ulid as ulid_lib

page_app = typer.Typer(help="Page operations")


@page_app.command("list")
def list_pages(
    workspace: str = typer.Option(None, help="Filter by workspace"),
    type: str = typer.Option(None, help="Filter by type"),
    limit: int = typer.Option(50, help="Max results"),
) -> None:
    """List pages."""
    from localnotion.config.settings import Settings
    from localnotion.core.index import PageIndex

    settings = Settings.load_yaml()
    index = PageIndex(settings.data_dir)

    pages = index.list_pages(workspace=workspace, page_type=type, limit=limit)

    table = Table(title="Pages")
    table.add_column("ID", style="dim", width=12)
    table.add_column("Title", style="bold")
    table.add_column("Type")
    table.add_column("Workspace")
    table.add_column("Tags")
    table.add_column("Modified")

    for p in pages:
        table.add_row(
            p.id[:12],
            p.title[:60],
            p.type,
            p.workspace,
            ", ".join(p.tags[:3]),
            p.modified_at.strftime("%Y-%m-%d"),
        )

    rprint(table)


@page_app.command("create")
def create_page(
    title: str = typer.Argument(...),
    type: str = typer.Option("page", help="Page type"),
    workspace: str = typer.Option("default", help="Workspace"),
    tags: str = typer.Option("", help="Comma-separated tags"),
) -> None:
    """Create a new page."""
    from localnotion.config.settings import Settings
    from localnotion.core.store import PageStore
    from localnotion.core.index import PageIndex
    from localnotion.core.models import Page

    settings = Settings.load_yaml()
    store = PageStore(settings.data_dir)
    index = PageIndex(settings.data_dir)

    page_id = str(ulid_lib.ULID())
    now = datetime.now(timezone.utc)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    page = Page(
        id=page_id, title=title, type=type, workspace=workspace,
        tags=tag_list, created_at=now, modified_at=now,
    )

    store.save(page)
    index.upsert_page(page)
    rprint(f"[green]Created page: {page_id}[/green] — {title}")


@page_app.command("search")
def search_pages(query: str = typer.Argument(...)) -> None:
    """Search pages by title."""
    from localnotion.config.settings import Settings
    from localnotion.core.index import PageIndex

    settings = Settings.load_yaml()
    index = PageIndex(settings.data_dir)

    results = index.search_titles(query)
    for p in results:
        rprint(f"  [dim]{p.id[:12]}[/dim]  [bold]{p.title}[/bold]  ({p.workspace})")


@page_app.command("show")
def show_page(page_id: str = typer.Argument(...)) -> None:
    """Show a page's content."""
    from localnotion.config.settings import Settings
    from localnotion.core.store import PageStore

    settings = Settings.load_yaml()
    store = PageStore(settings.data_dir)

    try:
        page = store.load(page_id)
        rprint(f"[bold]{page.title}[/bold] ({page.type})")
        rprint(f"[dim]Workspace: {page.workspace} | Tags: {', '.join(page.tags)}[/dim]")
        rprint("---")
        rprint(page.content)
    except FileNotFoundError:
        rprint(f"[red]Page not found: {page_id}[/red]")
