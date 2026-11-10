"""Compute cost, latency, marginal, and cost-per-point tables from unified logs."""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(.95 * len(ordered)))] if ordered else 0.0


def compute() -> dict:
    calls = [json.loads(line) for line in (ROOT / "runs/calls.jsonl").read_text().splitlines()]
    groups: dict[str, list[dict]] = defaultdict(list)
    items: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in calls:
        groups[row["component"]].append(row)
        items[(row["run_id"], row["item_id"])].append(row)
    by_component = {}
    for component, rows in groups.items():
        total_input = sum(x["input_tokens"] + x["cache_read_input_tokens"] for x in rows)
        by_component[component] = {
            "calls": len(rows),
            "mean_input_tokens": statistics.mean(x["input_tokens"] for x in rows),
            "mean_output_tokens": statistics.mean(x["output_tokens"] for x in rows),
            "mean_cached_tokens": statistics.mean(x["cache_read_input_tokens"] for x in rows),
            "cache_effectiveness": sum(x["cache_read_input_tokens"] for x in rows) / max(1, total_input),
            "mean_latency_ms": statistics.mean(x["latency_ms"] for x in rows),
            "mean_cost_usd": statistics.mean(x["cost_usd"] for x in rows),
        }
    per_component_item = {}
    for component in groups:
        component_items = [rows for rows in items.values() if rows and rows[0]["component"] == component]
        costs = [sum(x["cost_usd"] for x in rows) for rows in component_items]
        latencies = [sum(x["latency_ms"] for x in rows) for rows in component_items]
        per_component_item[component] = {"mean_cost_usd": statistics.mean(costs), "p95_cost_usd": p95(costs),
                                         "mean_latency_ms": statistics.mean(latencies), "p95_latency_ms": p95(latencies)}
    item_costs = [sum(x["cost_usd"] for x in rows) for rows in items.values()]
    item_latencies = [sum(x["latency_ms"] for x in rows) for rows in items.values()]
    audit = json.loads((ROOT / "runs/architecture-audit.json").read_text())
    stage_rows = audit["rows"]
    cost_per_point = []
    for previous, current in zip(stage_rows, stage_rows[1:]):
        delta_score = current["mean_score"] - previous["mean_score"]
        delta_cost = current["cost_per_item"] - previous["cost_per_item"]
        comparable = previous.get("scope", "").startswith("20 live items") and current.get("scope", "").startswith("20 live items")
        within = abs(delta_score) <= audit["noise_floor"]
        cost_per_point.append({"stage": current["stage"], "delta_score": delta_score,
                               "delta_cost_per_item": delta_cost,
                               "cost_per_point": None if not comparable or within or delta_score <= 0 else delta_cost / delta_score,
                               "verdict": "undefined — non-comparable scope" if not comparable else ("undefined — within noise" if within else ("regression" if delta_score < 0 else "measurable"))})
    m9 = json.loads((ROOT / "runs/graph-orchestrator-summary.json").read_text())
    graph_all = next(x for x in m9["persistent_world_model"] if x["subset"] == "all-items")
    graph_delta = graph_all["delta"]
    cost_per_point.append({"stage": "Graph (M9)", "delta_score": graph_delta,
                           "delta_cost_per_item": 0.0, "cost_per_point": None,
                           "verdict": "undefined — within noise" if abs(graph_delta) <= audit["noise_floor"] else "measurable"})
    planning_results = [json.loads(path.read_text()) for path in (ROOT / "runs/planning").glob("item-*/result.json")]
    plan_cost = sum(x["usage"]["cost_usd"] for x in planning_results)
    plan_steps = sum(x["steps_executed"] for x in planning_results)
    panel_results = [json.loads(path.read_text()) for path in (ROOT / "runs/panel").glob("item-*/result.json")]
    role_costs = [usage["cost_usd"] for result in panel_results for usage in result["role_usage"].values()]
    marginal = {
        "reflection_iteration": by_component.get("reflection", {}).get("mean_cost_usd", 0.0),
        "plan_step": plan_cost / max(1, plan_steps),
        "critic_role": statistics.mean(role_costs) if role_costs else 0.0,
        "graph_read": 0.0,
        "orchestrator_worker": 0.0,
    }
    return {"by_component": by_component, "per_component_item": per_component_item,
            "per_item": {"mean_cost_usd": statistics.mean(item_costs), "p95_cost_usd": p95(item_costs),
                         "mean_latency_ms": statistics.mean(item_latencies), "p95_latency_ms": p95(item_latencies)},
            "marginal_costs": marginal, "cost_per_point": cost_per_point,
            "noise_floor": audit["noise_floor"]}


def render(result: dict) -> str:
    lines = ["# Cost Model", "", "Generated from `runs/calls.jsonl`.", "",
             "## Per component", "", "| Component | Calls | Mean input | Mean output | Mean cached | Cache % | Mean latency ms | Mean cost |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, row in sorted(result["by_component"].items()):
        lines.append(f"| {name} | {row['calls']} | {row['mean_input_tokens']:.1f} | {row['mean_output_tokens']:.1f} | {row['mean_cached_tokens']:.1f} | {row['cache_effectiveness']:.1%} | {row['mean_latency_ms']:.1f} | ${row['mean_cost_usd']:.5f} |")
    lines += ["", "## Per item", "", "| Component | Mean cost | p95 cost | Mean latency ms | p95 latency ms |", "|---|---:|---:|---:|---:|"]
    for name, row in sorted(result["per_component_item"].items()):
        lines.append(f"| {name} | ${row['mean_cost_usd']:.5f} | ${row['p95_cost_usd']:.5f} | {row['mean_latency_ms']:.1f} | {row['p95_latency_ms']:.1f} |")
    lines += ["", "## Marginal costs", "", "| Unit | Cost |", "|---|---:|"]
    for name, value in result["marginal_costs"].items():
        lines.append(f"| {name.replace('_', ' ')} | ${value:.5f} |")
    lines += ["", "## Cost per point", "", "| Stage | Δ score | Δ cost/item | Cost/point | Verdict |", "|---|---:|---:|---:|---|"]
    for row in result["cost_per_point"]:
        cpp = "undefined" if row["cost_per_point"] is None else f"${row['cost_per_point']:.4f}"
        lines.append(f"| {row['stage']} | {row['delta_score']:+.4f} | ${row['delta_cost_per_item']:+.5f} | {cpp} | {row['verdict']} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    result = compute()
    (ROOT / "reports/cost_model.json").write_text(json.dumps(result, indent=2) + "\n")
    (ROOT / "reports/cost_model.md").write_text(render(result))
    print(json.dumps(result, indent=2))
