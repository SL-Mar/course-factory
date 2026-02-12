"""Pydantic schemas for the Course Factory API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# -- Setup wizard requests ---------------------------------------------------

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
    notion_api_key: str = ""
    github_token: str = ""
    ollama_model: str = "qwen2.5:14b"
    cloud_provider: str = "anthropic"
    cloud_model: str = "claude-sonnet-4-5-20250929"


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
    notion_api_key_set: bool = False
    github_token_set: bool = False
    ollama_model: str = ""
    cloud_provider: str = ""
    cloud_model: str = ""


class SaveResult(BaseModel):
    ok: bool
    path: str = ""
    error: str = ""


# -- Course schemas ----------------------------------------------------------

class CourseSource(BaseModel):
    type: str = Field(..., description="Source type: notion, github, or url")
    id: str = Field(default="", description="Notion page/DB ID")
    owner: str = Field(default="", description="GitHub owner")
    repo: str = Field(default="", description="GitHub repo name")
    url: str = Field(default="", description="Web URL")


class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    sources: list[CourseSource] = Field(default_factory=list)


class CourseResponse(BaseModel):
    id: str
    title: str
    description: str = ""
    sources: list[dict[str, Any]] = Field(default_factory=list)


class CourseListResponse(BaseModel):
    courses: list[dict[str, Any]]


# -- Workspace schemas -------------------------------------------------------

class FileTreeResponse(BaseModel):
    tree: list[dict[str, Any]]


class FileContentResponse(BaseModel):
    path: str
    content: str


class FileSaveRequest(BaseModel):
    path: str
    content: str


class StageStatusResponse(BaseModel):
    status: str = "idle"
    message: str = ""
    tokens: TokenUsageResponse | None = None


# -- Token tracking schemas --------------------------------------------------

class TokenUsageResponse(BaseModel):
    stage: str = ""
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class CourseTokensResponse(BaseModel):
    stages: dict[str, TokenUsageResponse] = Field(default_factory=dict)
    total: TokenUsageResponse | None = None
