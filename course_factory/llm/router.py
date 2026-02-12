"""LLM task router with VRAM management for local models."""

import logging
from typing import Any

from course_factory.llm.providers import (
    AnthropicProvider,
    LLMProvider,
    OllamaProvider,
    OpenAIProvider,
)

logger = logging.getLogger(__name__)

# Default task-to-model mapping.
# Each entry maps a task name to a (provider_name, model_name) tuple.
TASK_MODELS: dict[str, tuple[str, str]] = {
    "outline": ("ollama", "qwen2.5:14b"),
    "script_writing": ("ollama", "qwen2.5:14b"),
    "code_generation": ("ollama", "qwen2.5-coder:14b"),
    "quiz_generation": ("ollama", "qwen2.5:14b"),
    "review": ("anthropic", "claude-sonnet-4-5-20250929"),
    "summarize": ("ollama", "qwen2.5:14b"),
    "research": ("anthropic", "claude-sonnet-4-5-20250929"),
}


class LLMRouter:
    """Route LLM requests to the appropriate provider based on task type.

    Manages VRAM by ensuring only one local (Ollama) model is loaded at a time.
    Cloud providers (Anthropic, OpenAI) do not require VRAM management.
    """

    def __init__(self, settings: Any = None) -> None:
        self.settings = settings
        self._providers: dict[str, LLMProvider] = {}
        self._active_local_model: str | None = None
        logger.info("LLMRouter initialized")

    def _get_setting(self, key: str, default: Any = None) -> Any:
        """Retrieve a setting value, returning default if settings is None or key missing."""
        if self.settings is None:
            return default
        if hasattr(self.settings, key):
            return getattr(self.settings, key)
        if isinstance(self.settings, dict):
            return self.settings.get(key, default)
        return default

    def _resolve_task(self, task: str) -> tuple[str, str]:
        """Resolve a task name to a (provider_name, model_name) tuple."""
        if task in TASK_MODELS:
            return TASK_MODELS[task]
        logger.warning(
            "Unknown task '%s', falling back to 'outline' defaults", task
        )
        return TASK_MODELS["outline"]

    def _create_provider(self, provider_name: str, model: str) -> LLMProvider:
        """Instantiate a new provider for the given provider name and model."""
        if provider_name == "ollama":
            base_url = self._get_setting("ollama_base_url", "http://localhost:11434")
            timeout = self._get_setting("ollama_timeout", 600)
            return OllamaProvider(model=model, base_url=base_url, timeout=timeout)

        if provider_name == "anthropic":
            api_key = self._get_setting("anthropic_api_key", "")
            if not api_key:
                raise ValueError(
                    "Anthropic API key is required. Set 'anthropic_api_key' in settings."
                )
            timeout = self._get_setting("anthropic_timeout", 120)
            return AnthropicProvider(api_key=api_key, model=model, timeout=timeout)

        if provider_name == "openai":
            api_key = self._get_setting("openai_api_key", "")
            if not api_key:
                raise ValueError(
                    "OpenAI API key is required. Set 'openai_api_key' in settings."
                )
            timeout = self._get_setting("openai_timeout", 120)
            return OpenAIProvider(api_key=api_key, model=model, timeout=timeout)

        raise ValueError(f"Unknown provider: {provider_name}")

    async def get_provider(self, task: str) -> LLMProvider:
        """Get (or create) the appropriate provider for the given task.

        For local (Ollama) models, ensures only one model is loaded in VRAM
        at a time by unloading the previous model before loading a new one.
        """
        provider_name, model = self._resolve_task(task)
        cache_key = f"{provider_name}:{model}"

        # If we already have this exact provider cached, return it.
        if cache_key in self._providers:
            logger.debug("Returning cached provider for task '%s': %s", task, cache_key)
            return self._providers[cache_key]

        # VRAM management: unload previous local model if switching to a different one.
        if provider_name == "ollama" and self._active_local_model is not None:
            if self._active_local_model != cache_key:
                logger.info(
                    "Switching local model: unloading %s before loading %s",
                    self._active_local_model,
                    cache_key,
                )
                prev_provider = self._providers.get(self._active_local_model)
                if prev_provider is not None:
                    await prev_provider.unload()
                    del self._providers[self._active_local_model]
                self._active_local_model = None

        # Create and cache the new provider.
        logger.info("Creating provider for task '%s': %s", task, cache_key)
        provider = self._create_provider(provider_name, model)
        self._providers[cache_key] = provider

        if provider_name == "ollama":
            self._active_local_model = cache_key

        return provider

    async def chat(
        self,
        task: str,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Route a chat request to the appropriate provider for the task.

        Args:
            task: The task type (e.g. 'outline', 'code_generation', 'review').
            messages: List of chat messages with 'role' and 'content' keys.
            **kwargs: Additional arguments passed to the provider's chat method
                      (e.g. temperature, max_tokens).

        Returns:
            The LLM response text.
        """
        provider = await self.get_provider(task)
        logger.info(
            "Routing task '%s' to %s/%s",
            task,
            provider.get_provider_name(),
            provider.get_model_name(),
        )
        try:
            return await provider.chat(messages, **kwargs)
        except Exception:
            logger.error(
                "Chat failed for task '%s' on %s/%s",
                task,
                provider.get_provider_name(),
                provider.get_model_name(),
                exc_info=True,
            )
            raise

    async def unload_all(self) -> None:
        """Unload all local models and clear the provider cache."""
        logger.info("Unloading all providers")
        for cache_key, provider in list(self._providers.items()):
            if provider.get_provider_name() == "ollama":
                logger.info("Unloading local model: %s", cache_key)
                await provider.unload()
        self._providers.clear()
        self._active_local_model = None
        logger.info("All providers unloaded")
