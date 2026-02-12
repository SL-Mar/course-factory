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


# ---------------------------------------------------------------------------
# Pricing table  (USD per million tokens)
# Keys are prefix-matched against the model name.
# ---------------------------------------------------------------------------
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
    # Longest prefix match
    best_len = 0
    for prefix, (inp, out) in table.items():
        if model.startswith(prefix) and len(prefix) > best_len:
            input_rate, output_rate = inp, out
            best_len = len(prefix)
    return (
        usage.prompt_tokens * input_rate / 1_000_000
        + usage.completion_tokens * output_rate / 1_000_000
    )


# ---------------------------------------------------------------------------
# Per-stage accumulator
# ---------------------------------------------------------------------------
@dataclass
class StageTokenSummary:
    """Mutable accumulator for a single pipeline stage."""

    stage: str
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    def add_call(self, result: ChatResult) -> None:
        self.calls += 1
        self.prompt_tokens += result.usage.prompt_tokens
        self.completion_tokens += result.usage.completion_tokens
        self.total_tokens += result.usage.total_tokens
        self.estimated_cost_usd += estimate_cost(
            result.usage, result.provider, result.model
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
        }


# ---------------------------------------------------------------------------
# Persistence helper
# ---------------------------------------------------------------------------
def save_token_usage(
    workspace_dir: Path,
    stage_name: str,
    summary: StageTokenSummary,
) -> None:
    """Read/merge/write ``_tokens.json`` with a ``_total`` rollup."""
    tokens_path = Path(workspace_dir) / "_tokens.json"

    data: dict[str, Any] = {}
    if tokens_path.is_file():
        try:
            data = json.loads(tokens_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not read existing _tokens.json, starting fresh")

    data[stage_name] = summary.to_dict()

    # Recompute _total across all stages (skip _total itself)
    total_prompt = 0
    total_completion = 0
    total_all = 0
    total_cost = 0.0
    for key, val in data.items():
        if key.startswith("_"):
            continue
        total_prompt += val.get("prompt_tokens", 0)
        total_completion += val.get("completion_tokens", 0)
        total_all += val.get("total_tokens", 0)
        total_cost += val.get("estimated_cost_usd", 0.0)

    data["_total"] = {
        "prompt_tokens": total_prompt,
        "completion_tokens": total_completion,
        "total_tokens": total_all,
        "estimated_cost_usd": round(total_cost, 6),
    }

    tokens_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Saved token usage for stage '%s' to %s", stage_name, tokens_path)
