"""Consolidate Modules 1–6 without making new model calls."""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
NOISE = 0.06666666666666676


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower, upper = int(index), min(int(index) + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def row(name: str, score: float, tokens: float, cost: float, latencies: list[float] | None, scope: str) -> dict:
    return {
        "stage": name,
        "mean_score": score,
        "tokens_per_item": tokens,
        "cost_per_item": cost,
        "p50_latency_seconds": median(latencies) if latencies else None,
        "p95_latency_seconds": percentile(latencies, 0.95) if latencies else None,
        "cost_per_score_point": cost / score if score else None,
        "scope": scope,
    }


def main() -> None:
    baseline = load("runs/baseline/run-1/summary.json")
    base_items = [load(f"runs/baseline/run-1/item-{index:03}.json") for index in range(1, 21)]
    reflection = load("runs/reflection/summary.json")
    tools = load("runs/tools/summary.json")
    planning = load("runs/planning/summary.json")
    gen = load("runs/gen-critic/summary.json")
    panel = load("runs/panel/summary.json")
    chain = load("runs/chain/summary.json")["configurations"]["gated"]
    router = load("runs/router/summary.json")
    orchestrator = load("runs/orchestrator/summary.json")

    route_tokens = {}
    for item in base_items:
        route_tokens[("simple", item["id"])] = item["usage"]["input_tokens"] + item["usage"]["output_tokens"]
    for item in reflection["results"]:
        route_tokens[("standard", item["id"])] = item["usage"]["input_tokens"] + item["usage"]["output_tokens"]
    for item in planning["records"]:
        route_tokens[("complex", item["id"])] = item["usage"]["input_tokens"] + item["usage"]["output_tokens"]
    routed_tokens = mean(route_tokens[(record["destination"], record["id"])] for record in router["records"])
    routed_latencies = [record["latency_seconds"] for record in router["records"]]

    rows = [
        row("Zero-shot baseline", baseline["mean_score"], (baseline["input_tokens"] + baseline["output_tokens"]) / 20, baseline["cost_usd"] / 20, [x["latency_seconds"] for x in base_items], "20 live items"),
        row("Reflection (M2)", reflection["mean_score"], (reflection["input_tokens"] + reflection["output_tokens"]) / 20, reflection["cost_usd"] / 20, None, "20 live items; only mean latency retained"),
        row("Tool use (M3)", tools["mean_score"], (tools["input_tokens"] + tools["output_tokens"]) / 20, tools["cost_usd"] / 20, [x["latency_seconds"] for x in tools["results"]], "20 live items"),
        row("Planning (M4)", planning["mean_score"], (planning["input_tokens"] + planning["output_tokens"]) / 20, planning["cost_usd"] / 20, [x["latency_seconds"] for x in planning["records"]], "20 live items"),
        row("Generator–critic (M5)", gen["mean_score"], (gen["input_tokens"] + gen["output_tokens"]) / 3, gen["cost_usd"] / 3, None, "3 live items; forced three passes"),
        row("Review panel (M5)", panel["mean_score"], (panel["input_tokens"] + panel["output_tokens"]) / 3, panel["cost_usd"] / 3, [x["parallel_latency"] for x in panel["records"]], "3 live items; reviewer-phase latency"),
        row("Gated chain (M6)", chain["mean_score"], 0, 0, [0.0] * 20, "20-item offline replay; incremental tokens/cost"),
        row("Routed (M6)", router["comparison"]["routed"]["mean_score"], routed_tokens, router["comparison"]["routed"]["cost_usd"] / 20, routed_latencies, "20 frozen live route outputs"),
        row("Orchestrator (M6)", orchestrator["sectioning"]["sectioned"]["mean_score"], orchestrator["sectioning"]["sectioned"]["tokens"] / 3, panel["cost_usd"] / 3, [x["parallel_latency"] for x in panel["records"]], "3 frozen panel items"),
    ]
    previous = None
    for entry in rows:
        entry["delta_vs_previous"] = None if previous is None else entry["mean_score"] - previous
        entry["delta_exceeds_noise_floor"] = None if previous is None else entry["delta_vs_previous"] > NOISE
        previous = entry["mean_score"]

    output = {
        "noise_floor": NOISE,
        "rows": rows,
        "compound_progression_measured": [entry["mean_score"] for entry in rows],
        "comparable_full_set_progression": [baseline["mean_score"], reflection["mean_score"], tools["mean_score"], planning["mean_score"], chain["mean_score"], router["comparison"]["routed"]["mean_score"]],
        "new_api_cost_usd": 0.0,
    }
    path = ROOT / "runs/architecture-audit.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
