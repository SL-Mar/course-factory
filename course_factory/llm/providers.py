"""LLM provider implementations for Ollama, Anthropic, and OpenAI."""

import logging
from abc import ABC, abstractmethod
from typing import Any

import aiohttp
import httpx

from course_factory.llm.types import ChatResult, TokenUsage

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResult:
        """Send a chat completion request and return the response with usage."""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier."""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g. 'ollama', 'anthropic', 'openai')."""
        ...

    @abstractmethod
    async def unload(self) -> None:
        """Release resources (e.g. free VRAM for local models)."""
        ...


class OllamaProvider(LLMProvider):
    """Provider for locally-hosted Ollama models."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: int = 600,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        if self.base_url.endswith("/v1"):
            self.base_url = self.base_url[: -len("/v1")]
        self.timeout = timeout
        self.context_length: int = 32768
        self._context_length_fetched = False
        logger.info(
            "OllamaProvider initialized: model=%s base_url=%s timeout=%d",
            self.model,
            self.base_url,
            self.timeout,
        )

    async def _fetch_context_length(self) -> None:
        """Query the Ollama /api/show endpoint to discover context length."""
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
                        model_info = data.get("model_info", {})
                        for key, value in model_info.items():
                            if "context_length" in key:
                                self.context_length = int(value)
                                break
                        logger.info(
                            "Ollama model %s context_length=%d",
                            self.model,
                            self.context_length,
                        )
                    else:
                        logger.warning(
                            "Failed to fetch model info for %s (status %d), "
                            "using default context_length=%d",
                            self.model,
                            resp.status,
                            self.context_length,
                        )
        except Exception:
            logger.warning(
                "Could not query context length for %s, using default %d",
                self.model,
                self.context_length,
                exc_info=True,
            )
        self._context_length_fetched = True

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResult:
        """Send a chat request to the Ollama /api/chat endpoint."""
        await self._fetch_context_length()

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": self.context_length,
            },
        }

        logger.debug("Ollama chat request: model=%s messages=%d", self.model, len(messages))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        raise RuntimeError(
                            f"Ollama chat failed (status {resp.status}): {body}"
                        )
                    data = await resp.json()
                    content: str = data["message"]["content"]
                    prompt_tokens = data.get("prompt_eval_count", 0)
                    completion_tokens = data.get("eval_count", 0)
                    usage = TokenUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=prompt_tokens + completion_tokens,
                    )
                    logger.debug(
                        "Ollama chat response: model=%s length=%d tokens=%d",
                        self.model,
                        len(content),
                        usage.total_tokens,
                    )
                    return ChatResult(
                        text=content,
                        usage=usage,
                        provider="ollama",
                        model=self.model,
                    )
        except aiohttp.ClientError as exc:
            logger.error("Ollama chat network error: %s", exc)
            raise RuntimeError(f"Ollama chat network error: {exc}") from exc

    async def unload(self) -> None:
        """Send a request to Ollama to unload the model and free VRAM."""
        logger.info("Unloading Ollama model %s", self.model)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": "",
                        "keep_alive": "0",
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        logger.info("Ollama model %s unloaded successfully", self.model)
                    else:
                        body = await resp.text()
                        logger.warning(
                            "Ollama unload returned status %d: %s",
                            resp.status,
                            body,
                        )
        except Exception:
            logger.warning(
                "Failed to unload Ollama model %s", self.model, exc_info=True
            )

    async def check_health(self) -> bool:
        """Check if the Ollama server is reachable by querying /api/tags."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    healthy = resp.status == 200
                    logger.debug("Ollama health check: %s", "OK" if healthy else "FAIL")
                    return healthy
        except Exception:
            logger.debug("Ollama health check failed", exc_info=True)
            return False

    async def list_models(self) -> list[str]:
        """Return a list of model names available on the Ollama server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        logger.warning("Ollama list_models failed (status %d)", resp.status)
                        return []
                    data = await resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    logger.debug("Ollama available models: %s", models)
                    return models
        except Exception:
            logger.warning("Failed to list Ollama models", exc_info=True)
            return []

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "ollama"


class AnthropicProvider(LLMProvider):
    """Provider for the Anthropic Messages API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        timeout: int = 120,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        logger.info(
            "AnthropicProvider initialized: model=%s timeout=%d",
            self.model,
            self.timeout,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResult:
        """Send a chat request to the Anthropic Messages API."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # Anthropic requires a separate system parameter; extract it from messages.
        system_text: str | None = None
        chat_messages: list[dict[str, str]] = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                chat_messages.append(msg)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_text:
            payload["system"] = system_text

        logger.debug(
            "Anthropic chat request: model=%s messages=%d",
            self.model,
            len(chat_messages),
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Anthropic chat failed (status {resp.status_code}): {resp.text}"
                    )
                data = resp.json()
                content: str = data["content"][0]["text"]
                api_usage = data.get("usage", {})
                prompt_tokens = api_usage.get("input_tokens", 0)
                completion_tokens = api_usage.get("output_tokens", 0)
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )
                logger.debug(
                    "Anthropic chat response: model=%s length=%d tokens=%d",
                    self.model,
                    len(content),
                    usage.total_tokens,
                )
                return ChatResult(
                    text=content,
                    usage=usage,
                    provider="anthropic",
                    model=self.model,
                )
        except httpx.HTTPError as exc:
            logger.error("Anthropic chat network error: %s", exc)
            raise RuntimeError(f"Anthropic chat network error: {exc}") from exc

    async def unload(self) -> None:
        """No-op for cloud providers."""
        logger.debug("Anthropic unload called (no-op for cloud provider)")

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "anthropic"


class OpenAIProvider(LLMProvider):
    """Provider for the OpenAI Chat Completions API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        timeout: int = 120,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        logger.info(
            "OpenAIProvider initialized: model=%s timeout=%d",
            self.model,
            self.timeout,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResult:
        """Send a chat request to the OpenAI Chat Completions API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.debug(
            "OpenAI chat request: model=%s messages=%d",
            self.model,
            len(messages),
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"OpenAI chat failed (status {resp.status_code}): {resp.text}"
                    )
                data = resp.json()
                content: str = data["choices"][0]["message"]["content"]
                api_usage = data.get("usage", {})
                prompt_tokens = api_usage.get("prompt_tokens", 0)
                completion_tokens = api_usage.get("completion_tokens", 0)
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )
                logger.debug(
                    "OpenAI chat response: model=%s length=%d tokens=%d",
                    self.model,
                    len(content),
                    usage.total_tokens,
                )
                return ChatResult(
                    text=content,
                    usage=usage,
                    provider="openai",
                    model=self.model,
                )
        except httpx.HTTPError as exc:
            logger.error("OpenAI chat network error: %s", exc)
            raise RuntimeError(f"OpenAI chat network error: {exc}") from exc

    async def unload(self) -> None:
        """No-op for cloud providers."""
        logger.debug("OpenAI unload called (no-op for cloud provider)")

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "openai"
