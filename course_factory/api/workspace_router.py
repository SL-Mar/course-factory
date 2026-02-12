"""Workspace file-tree and pipeline stage router."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from course_factory.api.deps import get_workspace, get_settings
from course_factory.api.schemas import (
    CourseTokensResponse,
    FileTreeResponse,
    FileContentResponse,
    FileSaveRequest,
    StageStatusResponse,
    TokenUsageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses/{course_id}/workspace", tags=["workspace"])

# In-memory stage status tracking (keyed by course_id:stage_name)
_stage_status: dict[str, dict[str, Any]] = {}


@router.get("/tree", response_model=FileTreeResponse)
async def get_file_tree(course_id: str) -> FileTreeResponse:
    """Return recursive file tree for the workspace."""
    ws = get_workspace()
    try:
        tree = ws.get_tree(course_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Course not found")
    return FileTreeResponse(tree=tree)


@router.get("/file", response_model=FileContentResponse)
async def get_file(course_id: str, path: str = Query(...)) -> FileContentResponse:
    """Read file content from workspace."""
    ws = get_workspace()
    try:
        content = ws.read_file(course_id, path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    return FileContentResponse(path=path, content=content)


@router.put("/file")
async def save_file(course_id: str, req: FileSaveRequest) -> dict:
    """Save file content to workspace."""
    ws = get_workspace()
    try:
        ws.write_file(course_id, req.path, req.content)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    return {"ok": True}


@router.post("/stage/{stage_name}")
async def trigger_stage(course_id: str, stage_name: str) -> dict:
    """Trigger a pipeline stage as a background task."""
    key = f"{course_id}:{stage_name}"

    # Don't allow duplicate runs
    existing = _stage_status.get(key)
    if existing and existing.get("status") == "running":
        raise HTTPException(status_code=409, detail="Stage already running")

    _stage_status[key] = {"status": "running", "message": f"Starting {stage_name}..."}

    asyncio.create_task(_run_stage(course_id, stage_name, key))
    return {"ok": True, "status": "running"}


@router.get("/stage/{stage_name}/status", response_model=StageStatusResponse)
async def get_stage_status(course_id: str, stage_name: str) -> StageStatusResponse:
    """Poll stage progress."""
    key = f"{course_id}:{stage_name}"
    status = _stage_status.get(key, {"status": "idle", "message": ""})
    return StageStatusResponse(**status)


@router.get("/tokens", response_model=CourseTokensResponse)
async def get_course_tokens(course_id: str) -> CourseTokensResponse:
    """Return accumulated token usage across all stages."""
    ws = get_workspace()
    tokens_path = Path(ws._course_dir(course_id)) / "_tokens.json"
    if not tokens_path.is_file():
        return CourseTokensResponse()
    try:
        data = json.loads(tokens_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return CourseTokensResponse()

    stages: dict[str, TokenUsageResponse] = {}
    total: TokenUsageResponse | None = None
    for key, val in data.items():
        entry = TokenUsageResponse(**{k: val[k] for k in TokenUsageResponse.model_fields if k in val})
        if key == "_total":
            total = entry
        else:
            stages[key] = entry
    return CourseTokensResponse(stages=stages, total=total)


async def _run_stage(course_id: str, stage_name: str, key: str) -> None:
    """Execute a stage in the background."""
    try:
        if stage_name == "knowledge":
            from course_factory.knowledge.stage import KnowledgeStage

            stage = KnowledgeStage()
        elif stage_name == "discovery":
            from course_factory.discovery import DiscoveryStage

            stage = DiscoveryStage()
        elif stage_name == "research":
            from course_factory.research import ResearchStage

            stage = ResearchStage()
        elif stage_name == "synthesis":
            from course_factory.synthesis import SynthesisStage

            stage = SynthesisStage()
        else:
            _stage_status[key] = {
                "status": "error",
                "message": f"Unknown stage: {stage_name}",
            }
            return

        ws = get_workspace()
        settings = get_settings()
        manifest = ws.get_manifest(course_id)

        context = {
            "course_id": course_id,
            "sources": manifest.get("sources", []),
            "workspace_dir": str(ws._course_dir(course_id)),
            "settings": {
                "notion_api_key": settings.notion_api_key,
                "github_token": settings.github_token,
                "ollama_url": settings.ollama_url,
                "ollama_model": settings.ollama_model,
                "cloud_provider": settings.cloud_provider,
                "cloud_model": settings.cloud_model,
                "anthropic_api_key": settings.anthropic_api_key,
                "openai_api_key": settings.openai_api_key,
            },
        }

        if stage_name in ("research", "synthesis"):
            def _progress(msg: str) -> None:
                _stage_status[key] = {"status": "running", "message": msg}

            context["_progress_cb"] = _progress

        _stage_status[key] = {"status": "running", "message": f"Executing {stage_name}..."}
        context = await stage.execute(context)
        _stage_status[key] = {"status": "done", "message": f"{stage_name} complete"}

    except Exception as exc:
        logger.error("Stage %s failed for course %s: %s", stage_name, course_id, exc, exc_info=True)
        _stage_status[key] = {"status": "error", "message": str(exc)}
