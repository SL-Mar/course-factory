"""LLM provider implementations for Ollama, Anthropic, and OpenAI."""

import logging
from abc import ABC, abstractmethod
from typing import Any

import aiohttp
import httpx

from katja.ai.types import ChatResult, TokenUsage

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResult: ...

    @abstractmethod
    def get_model_name(self) -> str: ...

    @abstractmethod
    def get_provider_name(self) -> str: ...

    @abstractmethod
    async def unload(self) -> None: ...


class OllamaProvider(LLMProvider):
    """Provider for locally-hosted Ollama models."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434", timeout: int = 600) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        if self.base_url.endswith("/v1"):
            self.base_url = self.base_url[:-3]
        self.timeout = timeout
        self.context_length: int = 32768
        self._context_length_fetched = False

    async def _fetch_context_length(self) -> None:
        if self._context_length_fetched:
            return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/show",
                    json={"name": self.model},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for key, value in data.get("model_info", {}).items():
                            if "context_length" in key:
                                self.context_length = int(value)
                                break
        except Exception:
            pass
        self._context_length_fetched = True

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int = 4096) -> ChatResult:
        await self._fetch_context_length()
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens, "num_ctx": self.context_length},
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(f"Ollama chat failed ({resp.status}): {body}")
                data = await resp.json()
                content: str = data["message"]["content"]
                pt = data.get("prompt_eval_count", 0)
                ct = data.get("eval_count", 0)
                return ChatResult(text=content, usage=TokenUsage(pt, ct, pt + ct), provider="ollama", model=self.model)

    async def unload(self) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": "", "keep_alive": "0"},
                    timeout=aiohttp.ClientTimeout(total=30),
                )
        except Exception:
            pass

    async def check_health(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "ollama"


class AnthropicProvider(LLMProvider):
    """Provider for the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929", timeout: int = 120) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int = 4096) -> ChatResult:
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        system_text: str | None = None
        chat_messages: list[dict[str, str]] = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                chat_messages.append(msg)

        payload: dict[str, Any] = {"model": self.model, "messages": chat_messages, "temperature": temperature, "max_tokens": max_tokens}
        if system_text:
            payload["system"] = system_text

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Anthropic chat failed ({resp.status_code}): {resp.text}")
            data = resp.json()
            content: str = data["content"][0]["text"]
            u = data.get("usage", {})
            pt, ct = u.get("input_tokens", 0), u.get("output_tokens", 0)
            return ChatResult(text=content, usage=TokenUsage(pt, ct, pt + ct), provider="anthropic", model=self.model)

    async def unload(self) -> None:
        pass

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "anthropic"


class OpenAIProvider(LLMProvider):
    """Provider for the OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str = "gpt-4o", timeout: int = 120) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int = 4096) -> ChatResult:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI chat failed ({resp.status_code}): {resp.text}")
            data = resp.json()
            content: str = data["choices"][0]["message"]["content"]
            u = data.get("usage", {})
            pt, ct = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
            return ChatResult(text=content, usage=TokenUsage(pt, ct, pt + ct), provider="openai", model=self.model)

    async def unload(self) -> None:
        pass

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "openai"
