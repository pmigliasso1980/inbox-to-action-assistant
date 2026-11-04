"""Hand-written Anthropic tool loop with confirmation and complete tracing."""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

import anthropic

from agents.llm import MODEL, Usage, UsageLedger
from agents.review_tools import TOOLS, ToolError, execute_confirmed


def _usage(message: Any) -> Usage:
    raw = message.usage
    return Usage(raw.input_tokens, raw.output_tokens,
                 getattr(raw, "cache_read_input_tokens", 0) or 0,
                 getattr(raw, "cache_creation_input_tokens", 0) or 0)


def _blocks(content: Any) -> list[dict[str, Any]]:
    return [block.model_dump(mode="json") for block in content]


def _text(content: Any) -> str:
    return "\n".join(block.text for block in content if block.type == "text")


class ToolAgent:
    def __init__(self, *, max_steps: int = 8, trace_path: str | Path | None = None,
                 executor: Callable[[str, dict[str, Any]], Any] = execute_confirmed) -> None:
        self.max_steps = max_steps
        self.trace_path = Path(trace_path) if trace_path else None
        self.executor = executor

    def _write_trace(self, record: dict[str, Any]) -> None:
        if self.trace_path:
            self.trace_path.parent.mkdir(parents=True, exist_ok=True)
            with self.trace_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")

    def run(self, prompt: str, *, system: str | None = None, effort: str = "low") -> dict[str, Any]:
        client = anthropic.Anthropic(max_retries=2)
        history: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        ledger = UsageLedger()
        calls: list[dict[str, Any]] = []
        last_text = ""
        cap_hit = False
        for step in range(1, self.max_steps + 1):
            started = time.perf_counter()
            response = client.messages.create(
                model=MODEL, max_tokens=1600, output_config={"effort": effort},
                system=system or anthropic.NOT_GIVEN, tools=TOOLS, messages=history,
            )
            usage = _usage(response); ledger.add(usage, label=f"tool-turn-{step}", effort=effort)
            response_blocks = _blocks(response.content)
            last_text = _text(response.content) or last_text
            self._write_trace({"event": "assistant", "step": step, "stop_reason": response.stop_reason,
                               "content": response_blocks, "latency_ms": (time.perf_counter()-started)*1000,
                               "usage": asdict(usage)})
            if response.stop_reason == "pause_turn":
                history.append({"role": "assistant", "content": response_blocks})
                continue
            if response.stop_reason != "tool_use":
                return {"text": last_text, "steps": step, "cap_hit": False, "tool_calls": calls, "usage": ledger.summary()}
            history.append({"role": "assistant", "content": response_blocks})
            results: list[dict[str, Any]] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                record = {"step": step, "name": block.name, "arguments": block.input}
                try:
                    outcome = self.executor(block.name, block.input)
                    record.update({"result_summary": json.dumps(outcome.value)[:500],
                                   "confirmation": outcome.confirmation, "confirmed": outcome.confirmed,
                                   "latency_ms": outcome.latency_ms})
                    if not outcome.confirmed:
                        results.append({"type": "tool_result", "tool_use_id": block.id, "is_error": True,
                                        "content": f"Result rejected: {outcome.confirmation}"})
                    else:
                        results.append({"type": "tool_result", "tool_use_id": block.id,
                                        "content": json.dumps(outcome.value)})
                except (ToolError, TypeError, ValueError) as exc:
                    record.update({"result_summary": str(exc), "confirmation": "executor error", "confirmed": False,
                                   "latency_ms": 0.0})
                    results.append({"type": "tool_result", "tool_use_id": block.id, "is_error": True,
                                    "content": f"Tool {block.name} failed: {exc}"})
                record["token_usage_so_far"] = ledger.summary(); calls.append(record)
                self._write_trace({"event": "tool", **record})
            history.append({"role": "user", "content": results})
        cap_hit = True
        synthesis = client.messages.create(
            model=MODEL, max_tokens=900, output_config={"effort": effort}, system=system or anthropic.NOT_GIVEN,
            messages=history + [{"role": "user", "content": "The tool-step cap was reached. Synthesize the best supported final answer now without calling tools."}],
        )
        usage = _usage(synthesis); ledger.add(usage, label="cap-synthesis", effort=effort)
        return {"text": _text(synthesis.content) or last_text, "steps": self.max_steps,
                "cap_hit": cap_hit, "tool_calls": calls, "usage": ledger.summary()}
