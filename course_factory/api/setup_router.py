"""Setup wizard API endpoints."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from pathlib import Path

import httpx
from fastapi import APIRouter

from course_factory.api.schemas import (
    ConnectionResult,
    CurrentConfig,
    LicenseInfo,
    SaveConfigRequest,
    SaveResult,
    TestConnectionRequest,
    TestTelegramRequest,
    ValidateLicenseRequest,
)
from course_factory.config.settings import Settings
from course_factory.notifications.telegram import send_telegram

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["setup"])

_KEYS_DIR = Path(__file__).resolve().parents[2] / "keys"


# ---------------------------------------------------------------------------
# GET /api/setup/current
# ---------------------------------------------------------------------------
@router.get("/current")
async def get_current_config() -> CurrentConfig:
    """Return current config for pre-filling the wizard."""
    settings = Settings.load_yaml()
    return CurrentConfig(
        license_key=settings.license_key,
        ollama_url=settings.ollama_url,
        db_url=settings.db_url,
        qdrant_url=settings.qdrant_url,
        redis_url=settings.redis_url,
        anthropic_api_key_set=bool(settings.anthropic_api_key),
        openai_api_key_set=bool(settings.openai_api_key),
        telegram_webhook=settings.telegram_webhook,
        notion_api_key_set=bool(settings.notion_api_key),
        github_token_set=bool(settings.github_token),
    )


# ---------------------------------------------------------------------------
# POST /api/setup/validate-license
# ---------------------------------------------------------------------------
@router.post("/validate-license")
async def validate_license(req: ValidateLicenseRequest) -> LicenseInfo:
    """Validate a license key (base64url + file-based public key)."""
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError

    from course_factory.license.models import LicensePayload

    public_path = _KEYS_DIR / "public.key"
    if not public_path.exists():
        return LicenseInfo(valid=False, error="Public key not found on server.")

    try:
        raw_key = base64.b64decode(public_path.read_text(encoding="utf-8").strip())
        verify_key = VerifyKey(raw_key)
    except Exception as exc:
        return LicenseInfo(valid=False, error=f"Failed to load public key: {exc}")

    try:
        signed_bytes = base64.urlsafe_b64decode(req.license_key)
        payload_bytes = verify_key.verify(signed_bytes)
        payload = LicensePayload.from_json_bytes(payload_bytes)
    except BadSignatureError:
        return LicenseInfo(valid=False, error="Invalid signature.")
    except Exception as exc:
        return LicenseInfo(valid=False, error=f"Invalid key format: {exc}")

    return LicenseInfo(
        valid=True,
        email=payload.email,
        product=payload.product,
        tier=payload.tier,
        expiry=payload.expiry,
        is_expired=payload.is_expired,
    )


# ---------------------------------------------------------------------------
# POST /api/setup/test-connection
# ---------------------------------------------------------------------------
@router.post("/test-connection")
async def test_connection(req: TestConnectionRequest) -> ConnectionResult:
    """Test connectivity to a service."""
    tester = _CONNECTION_TESTERS.get(req.service)
    if not tester:
        return ConnectionResult(ok=False, service=req.service, message="Unknown service.")
    try:
        return await tester(req.url)
    except Exception as exc:
        return ConnectionResult(ok=False, service=req.service, message=str(exc))


async def _test_ollama(url: str) -> ConnectionResult:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{url.rstrip('/')}/api/tags")
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return ConnectionResult(
            ok=True,
            service="ollama",
            message=f"Connected — {len(models)} model(s) available.",
            details={"models": models},
        )


async def _test_db(url: str) -> ConnectionResult:
    from sqlalchemy import create_engine, text

    def _ping() -> None:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()

    await asyncio.to_thread(_ping)
    return ConnectionResult(ok=True, service="db", message="Connected.")


async def _test_qdrant(url: str) -> ConnectionResult:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{url.rstrip('/')}/collections")
        resp.raise_for_status()
        data = resp.json()
        collections = [c["name"] for c in data.get("result", {}).get("collections", [])]
        return ConnectionResult(
            ok=True,
            service="qdrant",
            message=f"Connected — {len(collections)} collection(s).",
            details={"collections": collections},
        )


async def _test_redis(url: str) -> ConnectionResult:
    import redis.asyncio as aioredis

    r = aioredis.from_url(url, socket_timeout=5.0)
    try:
        await r.ping()
    finally:
        await r.aclose()
    return ConnectionResult(ok=True, service="redis", message="Connected.")


_CONNECTION_TESTERS = {
    "ollama": _test_ollama,
    "db": _test_db,
    "qdrant": _test_qdrant,
    "redis": _test_redis,
}


# ---------------------------------------------------------------------------
# POST /api/setup/test-telegram
# ---------------------------------------------------------------------------
@router.post("/test-telegram")
async def test_telegram(req: TestTelegramRequest) -> ConnectionResult:
    """Send a test Telegram notification."""
    ok = await send_telegram(
        "Course Factory setup wizard — test notification.",
        webhook_url=req.webhook_url,
    )
    if ok:
        return ConnectionResult(ok=True, service="telegram", message="Message sent.")
    return ConnectionResult(ok=False, service="telegram", message="Webhook request failed.")


# ---------------------------------------------------------------------------
# POST /api/setup/save
# ---------------------------------------------------------------------------
@router.post("/save")
async def save_config(req: SaveConfigRequest) -> SaveResult:
    """Validate and persist the setup configuration to YAML."""
    # Build a Settings instance from the submitted values.
    try:
        settings = Settings(
            license_key=req.license_key,
            ollama_url=req.ollama_url,
            db_url=req.db_url,
            qdrant_url=req.qdrant_url,
            redis_url=req.redis_url,
            anthropic_api_key=req.anthropic_api_key,
            openai_api_key=req.openai_api_key,
            telegram_webhook=req.telegram_webhook,
            notion_api_key=req.notion_api_key,
            github_token=req.github_token,
        )
        yaml_path = settings.save_yaml()
        return SaveResult(ok=True, path=str(yaml_path))
    except Exception as exc:
        logger.exception("Failed to save config")
        return SaveResult(ok=False, error=str(exc))
