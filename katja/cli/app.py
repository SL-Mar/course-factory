"""Main Typer application and sub-command registration."""

from __future__ import annotations

import typer
from rich import print as rprint

import katja
from katja.cli.page_cmd import page_app
from katja.cli.table_cmd import table_app
from katja.cli.engine_cmd import engine_app
from katja.cli.import_cmd import import_app
from katja.cli.keygen_cmd import keygen_app
from katja.cli.config_cmd import config_app

app = typer.Typer(
    name="katja",
    help="Katja — Local-first knowledge operating system",
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
    """Print Katja version."""
    rprint(f"[bold cyan]Katja[/bold cyan] v{katja.__version__}")


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    """Start the Katja API server."""
    import uvicorn
    rprint(f"[bold green]Starting Katja server on {host}:{port}[/bold green]")
    uvicorn.run("katja.api.app:app", host=host, port=port, reload=False)


@app.command()
def reindex() -> None:
    """Rebuild the page index from disk."""
    from katja.config.settings import Settings
    from katja.core.store import PageStore
    from katja.core.index import PageIndex

    settings = Settings.load_yaml()
    store = PageStore(settings.data_dir)
    index = PageIndex(settings.data_dir)
    pages = store.list_all()
    count = index.rebuild_from_pages(pages)
    rprint(f"[green]Rebuilt index with {count} pages[/green]")


def app_main() -> None:
    app()
