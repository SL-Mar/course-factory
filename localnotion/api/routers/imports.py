"""Import API endpoints (Notion, Markdown)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from localnotion.api.deps import get_store, get_index
from localnotion.api.schemas import NotionImportRequest, MarkdownImportRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/import", tags=["import"])

_import_status: dict[str, dict[str, Any]] = {}


@router.post("/notion")
async def import_notion(req: NotionImportRequest) -> dict:
    if _import_status.get("notion", {}).get("status") == "running":
        raise HTTPException(status_code=409, detail="Notion import already running")

    _import_status["notion"] = {"status": "running", "message": "Starting Notion import..."}
    asyncio.create_task(_run_notion_import(req))
    return {"ok": True, "status": "running"}


@router.post("/markdown")
async def import_markdown(req: MarkdownImportRequest) -> dict:
    from localnotion.importers.markdown import MarkdownImporter

    store = get_store()
    index = get_index()
    importer = MarkdownImporter(store, index)

    try:
        stats = importer.import_directory(
            source_dir=req.source_dir,
            workspace=req.workspace,
            recursive=req.recursive,
        )
        return {"ok": True, **stats}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/status/{import_type}")
async def import_status(import_type: str) -> dict:
    return _import_status.get(import_type, {"status": "idle", "message": ""})


async def _run_notion_import(req: NotionImportRequest) -> None:
    try:
        from localnotion.importers.notion import NotionImporter

        store = get_store()
        index = get_index()
        importer = NotionImporter(token=req.token, store=store, index=index)

        stats = await importer.import_workspace(workspace=req.workspace)
        _import_status["notion"] = {"status": "done", "message": "Import complete", **stats}

    except Exception as exc:
        logger.error("Notion import failed: %s", exc, exc_info=True)
        _import_status["notion"] = {"status": "error", "message": str(exc)}
