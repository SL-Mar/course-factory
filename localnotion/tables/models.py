"""Table data models."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ColumnDef(BaseModel):
    """Definition of a single table column."""

    name: str
    type: Literal["text", "number", "date", "enum", "boolean", "url", "email", "relation"] = "text"
    required: bool = False
    default: Any = None
    options: list[str] = Field(default_factory=list, description="Enum options if type=enum")


class TableView(BaseModel):
    """A saved view configuration."""

    name: str
    type: Literal["table", "kanban", "calendar", "gallery"] = "table"
    group_by: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Literal["asc", "desc"] = "asc"
    filters: list[dict[str, Any]] = Field(default_factory=list)
    visible_columns: list[str] = Field(default_factory=list)


class TableSchema(BaseModel):
    """Full table definition."""

    name: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$", max_length=64)
    display_name: str
    columns: list[ColumnDef]
    default_view: str = "table"
    views: list[TableView] = Field(default_factory=list)
    page_links: bool = True


class TableRow(BaseModel):
    """A single row in a table."""

    id: int = 0
    data: dict[str, Any] = Field(default_factory=dict)
    page_id: Optional[str] = None
    created_at: str = ""
    modified_at: str = ""
