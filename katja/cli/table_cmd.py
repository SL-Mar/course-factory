"""Table management CLI commands."""

from __future__ import annotations

import json

import typer
from rich import print as rprint
from rich.table import Table as RichTable

table_app = typer.Typer(help="Table operations")


@table_app.command("list")
def list_tables() -> None:
    """List all tables."""
    from katja.config.settings import Settings
    from katja.tables.engine import TableEngine

    settings = Settings.load_yaml()
    engine = TableEngine(settings.data_dir)

    names = engine.list_tables()
    for name in names:
        schema = engine.get_schema(name)
        count = engine.count(name)
        rprint(f"  [bold]{schema.display_name if schema else name}[/bold] ({name}) — {count} rows")


@table_app.command("create")
def create_table(template: str = typer.Argument(..., help="Template name")) -> None:
    """Create a table from a template."""
    from katja.config.settings import Settings
    from katja.tables.engine import TableEngine
    from katja.tables.templates import get_template

    settings = Settings.load_yaml()
    engine = TableEngine(settings.data_dir)

    schema = get_template(template)
    if not schema:
        rprint(f"[red]Unknown template: {template}[/red]")
        from katja.tables.templates import list_template_names
        rprint(f"Available: {', '.join(list_template_names())}")
        raise typer.Exit(1)

    engine.create_table(schema)
    rprint(f"[green]Created table: {schema.display_name}[/green]")


@table_app.command("query")
def query_table(
    name: str = typer.Argument(...),
    limit: int = typer.Option(20),
) -> None:
    """Query rows from a table."""
    from katja.config.settings import Settings
    from katja.tables.engine import TableEngine

    settings = Settings.load_yaml()
    engine = TableEngine(settings.data_dir)

    schema = engine.get_schema(name)
    if not schema:
        rprint(f"[red]Table not found: {name}[/red]")
        raise typer.Exit(1)

    rows = engine.query(name, limit=limit)

    table = RichTable(title=schema.display_name)
    table.add_column("ID", style="dim")
    for col in schema.columns:
        table.add_column(col.name)

    for row in rows:
        values = [str(row.id)] + [str(row.data.get(c.name, "")) for c in schema.columns]
        table.add_row(*values)

    rprint(table)
