"""Setup wizard API endpoints."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter

from katja.api.deps import get_settings, reset_all
from katja.api.schemas import (
    ConnectionResult,
    LicenseInfo,
    SaveConfigRequest,
    SaveResult,
    TestConnectionRequest,
)
from katja.config.settings import Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["setup"])


@router.get("/current")
async def get_current_config() -> dict:
    s = get_settings()
    return {
        "license_key": s.license_key,
        "ollama_url": s.ollama_url,
        "qdrant_url": s.qdrant_url,
        "anthropic_api_key_set": bool(s.anthropic_api_key),
        "openai_api_key_set": bool(s.openai_api_key),
        "telegram_webhook": s.telegram_webhook,
        "notion_api_key_set": bool(s.notion_api_key),
        "ollama_model": s.ollama_model,
        "embed_model": s.embed_model,
        "cloud_provider": s.cloud_provider,
        "cloud_model": s.cloud_model,
        "data_dir": str(s.data_dir),
    }


@router.post("/test-connection")
async def test_connection(req: TestConnectionRequest) -> ConnectionResult:
    try:
        if req.service == "ollama":
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{req.url.rstrip('/')}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return ConnectionResult(ok=True, service="ollama", message=f"{len(models)} model(s)", details={"models": models})

        if req.service == "qdrant":
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{req.url.rstrip('/')}/collections")
                resp.raise_for_status()
                return ConnectionResult(ok=True, service="qdrant", message="Connected")

        return ConnectionResult(ok=False, service=req.service, message="Unknown service")
    except Exception as exc:
        return ConnectionResult(ok=False, service=req.service, message=str(exc))


@router.post("/save")
async def save_config(req: SaveConfigRequest) -> SaveResult:
    try:
        settings = Settings(
            license_key=req.license_key,
            ollama_url=req.ollama_url,
            qdrant_url=req.qdrant_url,
            anthropic_api_key=req.anthropic_api_key,
            openai_api_key=req.openai_api_key,
            telegram_webhook=req.telegram_webhook,
            notion_api_key=req.notion_api_key,
            ollama_model=req.ollama_model,
            embed_model=req.embed_model,
            cloud_provider=req.cloud_provider,
            cloud_model=req.cloud_model,
        )
        yaml_path = settings.save_yaml()
        reset_all()
        return SaveResult(ok=True, path=str(yaml_path))
    except Exception as exc:
        return SaveResult(ok=False, error=str(exc))
