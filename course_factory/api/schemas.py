"""Pydantic schemas for the setup wizard API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# -- Requests ----------------------------------------------------------------

class ValidateLicenseRequest(BaseModel):
    license_key: str = Field(..., description="Base64url-encoded license key")


class TestConnectionRequest(BaseModel):
    service: str = Field(
        ..., pattern="^(ollama|db|qdrant|redis)$",
        description="Service to test",
    )
    url: str = Field(..., description="Service URL / connection string")


class TestTelegramRequest(BaseModel):
    webhook_url: str = Field(..., description="Telegram webhook URL")


class SaveConfigRequest(BaseModel):
    license_key: str = ""
    ollama_url: str = "http://localhost:11434"
    db_url: str = "postgresql://cf:cf@localhost:5435/course_factory"
    qdrant_url: str = "http://localhost:6333"
    redis_url: str = "redis://localhost:6379/2"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    telegram_webhook: str = "http://localhost:5678/webhook/send-telegram"


# -- Responses ---------------------------------------------------------------

class LicenseInfo(BaseModel):
    valid: bool
    email: str = ""
    product: str = ""
    tier: str = ""
    expiry: str = ""
    is_expired: bool = False
    error: str = ""


class ConnectionResult(BaseModel):
    ok: bool
    service: str
    message: str
    details: dict | None = None


class CurrentConfig(BaseModel):
    license_key: str = ""
    ollama_url: str = ""
    db_url: str = ""
    qdrant_url: str = ""
    redis_url: str = ""
    anthropic_api_key_set: bool = False
    openai_api_key_set: bool = False
    telegram_webhook: str = ""


class SaveResult(BaseModel):
    ok: bool
    path: str = ""
    error: str = ""
