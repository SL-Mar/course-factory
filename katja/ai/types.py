"""LLM response types, token accounting, and cost estimation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TokenUsage:
    """Immutable token-count pair."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


@dataclass(frozen=True)
class ChatResult:
    """Value returned by every provider's ``chat()`` method."""

    text: str
    usage: TokenUsage
    provider: str
    model: str


MODEL_PRICING: dict[str, dict[str, tuple[float, float]]] = {
    "anthropic": {
        "claude-sonnet-4": (3.0, 15.0),
        "claude-haiku-3": (0.25, 1.25),
    },
    "openai": {
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.0),
    },
    "ollama": {},
}


def estimate_cost(usage: TokenUsage, provider: str, model: str) -> float:
    """Return estimated USD cost for a single call."""
    table = MODEL_PRICING.get(provider, {})
    input_rate = 0.0
    output_rate = 0.0
    best_len = 0
    for prefix, (inp, out) in table.items():
        if model.startswith(prefix) and len(prefix) > best_len:
            input_rate, output_rate = inp, out
            best_len = len(prefix)
    return (
        usage.prompt_tokens * input_rate / 1_000_000
        + usage.completion_tokens * output_rate / 1_000_000
    )
