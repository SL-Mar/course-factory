"""LLM task router with VRAM management for local models."""

import logging
from typing import Any

from localnotion.ai.providers import AnthropicProvider, LLMProvider, OllamaProvider, OpenAIProvider
from localnotion.ai.types import ChatResult

logger = logging.getLogger(__name__)

TASK_MODELS: dict[str, tuple[str, str]] = {
    # Knowledge management
    "summarize": ("ollama", "qwen2.5:14b"),
    "tag": ("ollama", "qwen2.5:14b"),
    "expand": ("ollama", "qwen2.5:14b"),
    "translate": ("ollama", "qwen2.5:14b"),
    "extract_entities": ("ollama", "qwen2.5:14b"),
    # Engines
    "outline": ("ollama", "qwen2.5:14b"),
    "script_writing": ("ollama", "qwen2.5:14b"),
    "slide_generation": ("ollama", "qwen2.5:14b"),
    "spec_writing": ("anthropic", "claude-sonnet-4-5-20250929"),
    "article_drafting": ("anthropic", "claude-sonnet-4-5-20250929"),
    "docs_generation": ("ollama", "qwen2.5:14b"),
    # Complex tasks
    "chat": ("ollama", "qwen2.5:14b"),
    "research": ("anthropic", "claude-sonnet-4-5-20250929"),
    "review": ("anthropic", "claude-sonnet-4-5-20250929"),
    "code_generation": ("ollama", "qwen2.5-coder:14b"),
}


class LLMRouter:
    """Route LLM requests to the appropriate provider based on task type."""

    def __init__(self, settings: Any = None) -> None:
        self.settings = settings
        self._providers: dict[str, LLMProvider] = {}
        self._active_local_model: str | None = None

    def _get_setting(self, key: str, default: Any = None) -> Any:
        if self.settings is None:
            return default
        if hasattr(self.settings, key):
            return getattr(self.settings, key)
        if isinstance(self.settings, dict):
            return self.settings.get(key, default)
        return default

    def _resolve_task(self, task: str) -> tuple[str, str]:
        if task not in TASK_MODELS:
            logger.warning("Unknown task '%s', falling back to 'chat'", task)
        default_provider, default_model = TASK_MODELS.get(task, TASK_MODELS["chat"])

        if default_provider == "ollama":
            override = self._get_setting("ollama_model", "")
            if override:
                return ("ollama", override)
            return (default_provider, default_model)

        override_provider = self._get_setting("cloud_provider", "")
        override_model = self._get_setting("cloud_model", "")
        return (override_provider or default_provider, override_model or default_model)

    def _create_provider(self, provider_name: str, model: str) -> LLMProvider:
        if provider_name == "ollama":
            base_url = self._get_setting("ollama_url", "http://localhost:11434")
            return OllamaProvider(model=model, base_url=base_url, timeout=self._get_setting("ollama_timeout", 600))
        if provider_name == "anthropic":
            api_key = self._get_setting("anthropic_api_key", "")
            if not api_key:
                raise ValueError("Anthropic API key required")
            return AnthropicProvider(api_key=api_key, model=model)
        if provider_name == "openai":
            api_key = self._get_setting("openai_api_key", "")
            if not api_key:
                raise ValueError("OpenAI API key required")
            return OpenAIProvider(api_key=api_key, model=model)
        raise ValueError(f"Unknown provider: {provider_name}")

    async def get_provider(self, task: str) -> LLMProvider:
        provider_name, model = self._resolve_task(task)
        cache_key = f"{provider_name}:{model}"

        if cache_key in self._providers:
            return self._providers[cache_key]

        if provider_name == "ollama" and self._active_local_model and self._active_local_model != cache_key:
            prev = self._providers.get(self._active_local_model)
            if prev:
                await prev.unload()
                del self._providers[self._active_local_model]
            self._active_local_model = None

        provider = self._create_provider(provider_name, model)
        self._providers[cache_key] = provider
        if provider_name == "ollama":
            self._active_local_model = cache_key
        return provider

    async def chat(self, task: str, messages: list[dict[str, str]], **kwargs: Any) -> ChatResult:
        provider = await self.get_provider(task)
        return await provider.chat(messages, **kwargs)

    async def unload_all(self) -> None:
        for provider in self._providers.values():
            if provider.get_provider_name() == "ollama":
                await provider.unload()
        self._providers.clear()
        self._active_local_model = None
