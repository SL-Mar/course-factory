"""Pre-built table templates."""

from __future__ import annotations

from katja.tables.models import ColumnDef, TableSchema, TableView

TEMPLATES: dict[str, TableSchema] = {
    "product_tracker": TableSchema(
        name="product_tracker",
        display_name="Product Tracker",
        columns=[
            ColumnDef(name="name", type="text", required=True),
            ColumnDef(name="status", type="enum", options=["idea", "active", "maintenance", "deprecated"]),
            ColumnDef(name="priority", type="enum", options=["low", "medium", "high", "critical"]),
            ColumnDef(name="revenue_target", type="number"),
            ColumnDef(name="last_updated", type="date"),
        ],
        views=[
            TableView(name="All Products", type="table"),
            TableView(name="By Status", type="kanban", group_by="status"),
        ],
    ),
    "article_pipeline": TableSchema(
        name="article_pipeline",
        display_name="Article Pipeline",
        columns=[
            ColumnDef(name="title", type="text", required=True),
            ColumnDef(name="status", type="enum", options=["idea", "draft", "editing", "published"]),
            ColumnDef(name="priority", type="enum", options=["low", "medium", "high"]),
            ColumnDef(name="domain", type="text"),
            ColumnDef(name="url", type="url"),
            ColumnDef(name="published_date", type="date"),
        ],
        views=[
            TableView(name="Pipeline", type="kanban", group_by="status"),
            TableView(name="Calendar", type="calendar"),
        ],
    ),
    "customer_database": TableSchema(
        name="customer_database",
        display_name="Customer Database",
        columns=[
            ColumnDef(name="email", type="email", required=True),
            ColumnDef(name="product", type="text"),
            ColumnDef(name="license_key", type="text"),
            ColumnDef(name="amount", type="number"),
            ColumnDef(name="issued_at", type="date"),
            ColumnDef(name="is_active", type="boolean", default=True),
        ],
        views=[TableView(name="All Customers", type="table")],
    ),
    "vessel_registry": TableSchema(
        name="vessel_registry",
        display_name="Vessel Registry",
        columns=[
            ColumnDef(name="imo", type="text", required=True),
            ColumnDef(name="mmsi", type="text"),
            ColumnDef(name="name", type="text", required=True),
            ColumnDef(name="vessel_type", type="text"),
            ColumnDef(name="flag", type="text"),
            ColumnDef(name="dwt", type="number"),
            ColumnDef(name="built_year", type="number"),
            ColumnDef(name="fleet", type="text"),
        ],
        views=[
            TableView(name="All Vessels", type="table"),
            TableView(name="Gallery", type="gallery"),
        ],
    ),
    "spec_registry": TableSchema(
        name="spec_registry",
        display_name="Spec Registry",
        columns=[
            ColumnDef(name="spec_id", type="text", required=True),
            ColumnDef(name="title", type="text", required=True),
            ColumnDef(name="product", type="text"),
            ColumnDef(name="status", type="enum", options=["draft", "review", "approved", "implemented"]),
            ColumnDef(name="depends_on", type="text"),
            ColumnDef(name="effort_days", type="number"),
        ],
        views=[
            TableView(name="All Specs", type="table"),
            TableView(name="By Status", type="kanban", group_by="status"),
        ],
    ),
    "reading_list": TableSchema(
        name="reading_list",
        display_name="Reading List",
        columns=[
            ColumnDef(name="title", type="text", required=True),
            ColumnDef(name="author", type="text"),
            ColumnDef(name="url", type="url"),
            ColumnDef(name="status", type="enum", options=["to_read", "reading", "done"]),
            ColumnDef(name="tags", type="text"),
            ColumnDef(name="notes", type="text"),
        ],
        views=[
            TableView(name="All Items", type="table"),
            TableView(name="By Status", type="kanban", group_by="status"),
        ],
    ),
}


def get_template(name: str) -> TableSchema | None:
    """Get a table template by name."""
    return TEMPLATES.get(name)


def list_template_names() -> list[str]:
    """List all available template names."""
    return list(TEMPLATES.keys())
