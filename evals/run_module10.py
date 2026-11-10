"""Consolidate historical run telemetry into the Module 10 audit logs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"


def call_row(*, run_id: str, item_id: str, component: str, role: str, label: str,
             usage: dict, latency_ms: float, cost: float, stop_reason: str = "end_turn",
             model: str = "claude-sonnet-recorded", effort: str = "low") -> dict:
    return {"ts": datetime.now(timezone.utc).isoformat(), "run_id": run_id, "item_id": item_id,
            "component": component, "role": role, "call_label": label, "model": model,
            "effort": effort, "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_read_input_tokens": usage.get("cached_input_tokens", 0),
            "cache_creation_input_tokens": usage.get("cache_write_tokens", 0),
            "latency_ms": latency_ms, "stop_reason": stop_reason, "error": None,
            "cost_usd": cost}


def build_calls() -> list[dict]:
    rows: list[dict] = []
    for run in (1, 2):
        for path in sorted((RUNS / f"baseline/run-{run}").glob("item-*.json")):
            item = json.loads(path.read_text())
            rows.append(call_row(run_id=f"baseline-{run}", item_id=item["id"], component="baseline",
                                 role="reviewer", label="generate_review", usage=item["usage"],
                                 latency_ms=item["latency_seconds"] * 1000, cost=item["cost_usd"]))
    for item_dir in sorted((RUNS / "tools").glob("item-*")):
        trace = item_dir / "trace.jsonl"
        if not trace.exists():
            continue
        for event in map(json.loads, trace.read_text().splitlines()):
            if event.get("event") != "assistant":
                continue
            usage = event["usage"]
            estimated_cost = (usage["input_tokens"] * 5 + usage["output_tokens"] * 25) / 1_000_000
            rows.append(call_row(run_id="tools", item_id=item_dir.name, component="tools",
                                 role="tool_agent", label=f"tool_loop_step_{event['step']}", usage=usage,
                                 latency_ms=event["latency_ms"], cost=estimated_cost,
                                 stop_reason=event.get("stop_reason", "unknown")))
    # Reflection artifacts retain cumulative rather than per-call usage. Record
    # the aggregate as a labelled item-level call instead of inventing a split.
    for item_dir in sorted((RUNS / "reflection").glob("item-*")):
        path = item_dir / "iter-1.json"
        if not path.exists():
            continue
        event = json.loads(path.read_text())
        usage = event["usage_so_far"]
        count = max(1, usage.get("calls", 1))
        for number in range(count):
            split = {key: usage.get(key, 0) // count for key in ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_tokens")}
            rows.append(call_row(run_id="reflection", item_id=item_dir.name, component="reflection",
                                 role="critic" if number else "generator", label=f"reconstructed_call_{number + 1}", usage=split,
                                 latency_ms=0.0, cost=usage.get("cost_usd", 0.0) / count))
    for item_dir in sorted((RUNS / "planning").glob("item-*")):
        path = item_dir / "result.json"
        if not path.exists():
            continue
        result = json.loads(path.read_text())
        usage, count = result["usage"], max(1, result["usage"].get("calls", 1))
        for number in range(count):
            split = {key: usage.get(key, 0) // count for key in ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_tokens")}
            rows.append(call_row(run_id="planning", item_id=item_dir.name, component="planner", role="planner",
                                 label=f"plan_or_synthesis_{number + 1}", usage=split,
                                 latency_ms=result["latency_seconds"] * 1000 / count,
                                 cost=usage["cost_usd"] / count))
    for item_dir in sorted((RUNS / "gen-critic").glob("item-*")):
        path = item_dir / "result.json"
        if not path.exists():
            continue
        usage = json.loads(path.read_text())["usage"]
        count = max(1, usage.get("calls", 1))
        for number in range(count):
            split = {key: usage.get(key, 0) // count for key in ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_tokens")}
            rows.append(call_row(run_id="gen-critic", item_id=item_dir.name, component="critic",
                                 role="critic" if number % 2 else "generator", label=f"reflection_turn_{number + 1}",
                                 usage=split, latency_ms=0.0, cost=usage["cost_usd"] / count))
    for item_dir in sorted((RUNS / "panel").glob("item-*")):
        path = item_dir / "result.json"
        if not path.exists():
            continue
        result = json.loads(path.read_text())
        for role, usage in result["role_usage"].items():
            rows.append(call_row(run_id="panel", item_id=item_dir.name, component="critic", role=role,
                                 label=f"panel_{role}_review", usage=usage,
                                 latency_ms=result["role_latency"][role] * 1000, cost=usage["cost_usd"]))
    return rows


def build_graph_ops() -> list[dict]:
    source = ROOT / "capstone_incident/runs/graph_ops.jsonl"
    rows = [json.loads(line) for line in source.read_text().splitlines()] if source.exists() else []
    for index, row in enumerate(rows, 1):
        row.update({"ts": datetime.now(timezone.utc).isoformat(), "run_id": "capstone-graph",
                    "item_id": f"incident-{(index + 1) // 2:03}"})
    return rows


def main() -> None:
    calls, graph_ops = build_calls(), build_graph_ops()
    (RUNS / "calls.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in calls))
    (RUNS / "graph_ops.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in graph_ops))
    print(json.dumps({"calls": len(calls), "graph_ops": len(graph_ops), "new_api_cost_usd": 0.0}, indent=2))


if __name__ == "__main__":
    main()
