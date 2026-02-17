"""Table CRUD + query API endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from katja.api.deps import get_tables, get_index
from katja.api.schemas import (
    TableCreateRequest,
    RowCreateRequest,
    RowUpdateRequest,
    TableQueryRequest,
)
from katja.tables.models import ColumnDef, TableSchema, TableView
from katja.tables.templates import get_template, list_template_names

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tables", tags=["tables"])


@router.get("")
async def list_tables() -> list[dict]:
    engine = get_tables()
    names = engine.list_tables()
    result = []
    for name in names:
        schema = engine.get_schema(name)
        count = engine.count(name)
        result.append({
            "name": name,
            "display_name": schema.display_name if schema else name,
            "columns": len(schema.columns) if schema else 0,
            "rows": count,
        })
    return result


@router.get("/templates")
async def get_templates() -> list[str]:
    return list_template_names()


@router.post("")
async def create_table(req: TableCreateRequest) -> dict:
    engine = get_tables()
    index = get_index()

    if req.template:
        schema = get_template(req.template)
        if not schema:
            raise HTTPException(status_code=400, detail=f"Unknown template: {req.template}")
    elif req.name and req.columns:
        columns = [ColumnDef(**c) for c in req.columns]
        schema = TableSchema(
            name=req.name,
            display_name=req.display_name or req.name,
            columns=columns,
        )
    else:
        raise HTTPException(status_code=400, detail="Provide 'template' or 'name' + 'columns'")

    engine.create_table(schema)
    index.register_table(
        name=schema.name,
        display_name=schema.display_name,
        schema_def=schema.model_dump(),
        db_path=str(engine._db_path(schema.name)),
    )

    return {"ok": True, "name": schema.name}


@router.get("/{table_name}")
async def get_table(table_name: str) -> dict:
    engine = get_tables()
    schema = engine.get_schema(table_name)
    if not schema:
        raise HTTPException(status_code=404, detail="Table not found")
    return {
        "name": schema.name,
        "display_name": schema.display_name,
        "columns": [c.model_dump() for c in schema.columns],
        "views": [v.model_dump() for v in schema.views],
        "rows": engine.count(table_name),
    }


@router.delete("/{table_name}")
async def delete_table(table_name: str) -> dict:
    get_tables().delete_table(table_name)
    return {"ok": True}


@router.post("/{table_name}/query")
async def query_table(table_name: str, req: TableQueryRequest) -> list[dict]:
    engine = get_tables()
    if not engine.get_schema(table_name):
        raise HTTPException(status_code=404, detail="Table not found")
    rows = engine.query(
        table_name, where=req.where, order_by=req.order_by,
        order_dir=req.order_dir, limit=req.limit, offset=req.offset,
    )
    return [{"id": r.id, **r.data, "page_id": r.page_id, "created_at": r.created_at, "modified_at": r.modified_at} for r in rows]


@router.post("/{table_name}/rows")
async def insert_row(table_name: str, req: RowCreateRequest) -> dict:
    engine = get_tables()
    if not engine.get_schema(table_name):
        raise HTTPException(status_code=404, detail="Table not found")
    row_id = engine.insert_row(table_name, req.data, page_id=req.page_id)
    return {"ok": True, "id": row_id}


@router.patch("/{table_name}/rows/{row_id}")
async def update_row(table_name: str, row_id: int, req: RowUpdateRequest) -> dict:
    engine = get_tables()
    engine.update_row(table_name, row_id, req.data)
    return {"ok": True}


@router.delete("/{table_name}/rows/{row_id}")
async def delete_row(table_name: str, row_id: int) -> dict:
    engine = get_tables()
    engine.delete_row(table_name, row_id)
    return {"ok": True}
