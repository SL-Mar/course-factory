"""Main Typer application and sub-command registration."""

from __future__ import annotations

import typer
from rich import print as rprint

import localnotion
from localnotion.cli.page_cmd import page_app
from localnotion.cli.table_cmd import table_app
from localnotion.cli.engine_cmd import engine_app
from localnotion.cli.import_cmd import import_app
from localnotion.cli.keygen_cmd import keygen_app
from localnotion.cli.config_cmd import config_app

app = typer.Typer(
    name="localnotion",
    help="LocalNotion — Local-first knowledge operating system",
    add_completion=False,
)

app.add_typer(page_app, name="page")
app.add_typer(table_app, name="table")
app.add_typer(engine_app, name="engine")
app.add_typer(import_app, name="import")
app.add_typer(keygen_app, name="keygen")
app.add_typer(config_app, name="config")


@app.command()
def version() -> None:
    """Print LocalNotion version."""
    rprint(f"[bold cyan]LocalNotion[/bold cyan] v{localnotion.__version__}")


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    """Start the LocalNotion API server."""
    import uvicorn
    rprint(f"[bold green]Starting LocalNotion server on {host}:{port}[/bold green]")
    uvicorn.run("localnotion.api.app:app", host=host, port=port, reload=False)


@app.command()
def reindex() -> None:
    """Rebuild the page index from disk."""
    from localnotion.config.settings import Settings
    from localnotion.core.store import PageStore
    from localnotion.core.index import PageIndex

    settings = Settings.load_yaml()
    store = PageStore(settings.data_dir)
    index = PageIndex(settings.data_dir)
    pages = store.list_all()
    count = index.rebuild_from_pages(pages)
    rprint(f"[green]Rebuilt index with {count} pages[/green]")


def app_main() -> None:
    app()
