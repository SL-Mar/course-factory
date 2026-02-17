"""Engine execution API endpoints."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from katja.api.deps import get_store, get_index, get_llm_router
from katja.api.schemas import EngineRunRequest, EngineStatusResponse
from katja.engines.base import EngineContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/engines", tags=["engines"])

_engine_status: dict[str, dict[str, Any]] = {}


@router.get("")
async def list_engines() -> list[dict]:
    return [
        {"name": "course", "display_name": "Course Engine", "description": "Generate courses from knowledge"},
        {"name": "spec", "display_name": "Spec Engine", "description": "Generate technical specifications"},
        {"name": "article", "display_name": "Article Engine", "description": "Draft technical articles"},
        {"name": "docs", "display_name": "Docs Engine", "description": "Generate product documentation"},
    ]


@router.post("/run")
async def run_engine(req: EngineRunRequest) -> dict:
    key = f"{req.engine}:{req.workspace}"

    existing = _engine_status.get(key)
    if existing and existing.get("status") == "running":
        raise HTTPException(status_code=409, detail="Engine already running")

    _engine_status[key] = {"status": "running", "message": f"Starting {req.engine} engine..."}
    asyncio.create_task(_execute_engine(req, key))
    return {"ok": True, "status": "running"}


@router.get("/status/{engine_name}")
async def engine_status(engine_name: str, workspace: str = "default") -> EngineStatusResponse:
    key = f"{engine_name}:{workspace}"
    status = _engine_status.get(key, {"status": "idle", "message": ""})
    return EngineStatusResponse(**status)


@router.get("/runs")
async def list_runs(engine: str | None = None, limit: int = 50) -> list[dict]:
    index = get_index()
    return index.list_engine_runs(engine=engine, limit=limit)


async def _execute_engine(req: EngineRunRequest, key: str) -> None:
    try:
        store = get_store()
        index = get_index()
        llm_router = get_llm_router()

        def progress(msg: str) -> None:
            _engine_status[key] = {"status": "running", "message": msg}

        ctx = EngineContext(
            store=store,
            index=index,
            router=llm_router,
            workspace=req.workspace,
            progress_cb=progress,
        )

        if req.engine == "course":
            from katja.engines.course import CourseEngine
            engine = CourseEngine()
        elif req.engine == "spec":
            from katja.engines.spec import SpecEngine
            engine = SpecEngine()
        elif req.engine == "article":
            from katja.engines.article import ArticleEngine
            engine = ArticleEngine()
        elif req.engine == "docs":
            from katja.engines.docs import DocsEngine
            engine = DocsEngine()
        else:
            _engine_status[key] = {"status": "error", "message": f"Unknown engine: {req.engine}"}
            return

        result = await engine.execute(ctx, **req.params)
        _engine_status[key] = {"status": "done", "message": f"{req.engine} complete", "result": result}

    except Exception as exc:
        logger.error("Engine %s failed: %s", req.engine, exc, exc_info=True)
        _engine_status[key] = {"status": "error", "message": str(exc)}
