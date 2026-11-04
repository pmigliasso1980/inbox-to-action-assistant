"""Thin shared Anthropic client with normalized usage and cost accounting."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")
INPUT_PRICE_PER_M = 5.00
OUTPUT_PRICE_PER_M = 25.00
T = TypeVar("T", bound=BaseModel)


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def cost_usd(self) -> float:
        # These labs do not enable prompt caching, so all input uses the listed rate.
        return (self.input_tokens * INPUT_PRICE_PER_M + self.output_tokens * OUTPUT_PRICE_PER_M) / 1_000_000


class UsageLedger:
    def __init__(self, log_path: str | Path | None = None) -> None:
        self.calls: list[Usage] = []
        self.log_path = Path(log_path) if log_path else None

    def add(self, usage: Usage, *, label: str = "call", effort: str = "high") -> None:
        self.calls.append(usage)
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            record = {"timestamp": datetime.now(timezone.utc).isoformat(), "label": label,
                      "effort": effort, "model": MODEL, **asdict(usage), "cost_usd": usage.cost_usd}
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")

    def summary(self) -> dict[str, Any]:
        return {
            "calls": len(self.calls),
            "input_tokens": sum(u.input_tokens for u in self.calls),
            "output_tokens": sum(u.output_tokens for u in self.calls),
            "cached_input_tokens": sum(u.cached_input_tokens for u in self.calls),
            "cache_write_tokens": sum(u.cache_write_tokens for u in self.calls),
            "cost_usd": sum(u.cost_usd for u in self.calls),
        }


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(max_retries=2)


def _usage(message: Any) -> Usage:
    raw = message.usage
    return Usage(
        input_tokens=raw.input_tokens,
        output_tokens=raw.output_tokens,
        cached_input_tokens=getattr(raw, "cache_read_input_tokens", 0) or 0,
        cache_write_tokens=getattr(raw, "cache_creation_input_tokens", 0) or 0,
    )


def count_tokens(prompt: str) -> int:
    result = _client().messages.count_tokens(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return result.input_tokens


def call(prompt: str, *, max_tokens: int = 1000, effort: str = "high", system: str | None = None) -> tuple[str, Usage]:
    message = _client().messages.create(
        model=MODEL, max_tokens=max_tokens, output_config={"effort": effort},
        system=system or anthropic.NOT_GIVEN, messages=[{"role": "user", "content": prompt}],
    )
    text = next(block.text for block in message.content if block.type == "text")
    return text, _usage(message)


def call_json(prompt: str, schema: type[T], *, max_tokens: int = 1000,
              effort: str = "high", system: str | None = None) -> tuple[T, Usage]:
    message = _client().messages.parse(
        model=MODEL, max_tokens=max_tokens, output_config={"effort": effort}, output_format=schema,
        system=system or anthropic.NOT_GIVEN, messages=[{"role": "user", "content": prompt}],
    )
    if message.parsed_output is None:
        raise ValueError("Model returned no parsed structured output")
    return message.parsed_output, _usage(message)
