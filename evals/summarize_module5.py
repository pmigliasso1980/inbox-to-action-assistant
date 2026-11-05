"""Combine existing Module 5 runs into the token-budget comparison.

The one-pass row is derived from iteration 1 of the forced three-pass run, so
the comparison does not spend money repeating an identical API call.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / "runs" / name / "summary.json").read_text())


def first_pass(gen_critic: dict) -> dict:
    tokens = cached = 0
    cost = 0.0
    scores = []
    for result in gen_critic["results"]:
        scores.append(result["records"][0]["score"]["score"])
        trace = ROOT / "runs" / "gen-critic" / result["id"] / "transcript.jsonl"
        events = [json.loads(line) for line in trace.read_text().splitlines() if line]
        for event in events:
            if event["role"] in {"generator-1", "critic-1"}:
                usage = event["usage"]
                tokens += usage["input_tokens"] + usage["output_tokens"]
                cached += usage["cached_input_tokens"]
                cost += usage["input_tokens"] * 5 / 1_000_000
                cost += usage["output_tokens"] * 25 / 1_000_000
                cost += usage["cached_input_tokens"] * 0.5 / 1_000_000
                cost += usage["cache_write_tokens"] * 6.25 / 1_000_000
    items = len(scores)
    return {
        "configuration": "1 critic, combined rubric, 1 pass",
        "tokens_per_item": tokens / items,
        "cached_tokens_per_item": cached / items,
        "mean_score": sum(scores) / items,
        "cost_usd": cost,
        "source": "Derived from iteration 1 of runs/gen-critic; no duplicate calls.",
    }


def row(label: str, data: dict) -> dict:
    items = data["items"]
    tokens = data.get("tokens_per_item")
    if tokens is None:
        tokens = (data["input_tokens"] + data["output_tokens"]) / items
    return {
        "configuration": label,
        "tokens_per_item": tokens,
        "cached_tokens_per_item": data.get("cached_tokens", 0) / items,
        "mean_score": data["mean_score"],
        "cost_usd": data["cost_usd"],
    }


def main() -> None:
    gen = load("gen-critic")
    panel = load("panel")
    best = load("best-of-3")
    output = {
        "scope": "First three fixed evaluation items; primary-path tokens only.",
        "residual_difference": (
            "Artifacts have different schemas and output lengths, so exact token matching is not "
            "possible. Observed tokens/item are reported instead of treating agent count as budget."
        ),
        "configurations": [
            first_pass(gen),
            row("1 critic, combined rubric, 3 sequential passes", gen),
            row("3 critics, distinct rubrics, parallel", panel),
            row("best-of-3 generation, 1 critic", best),
        ],
    }
    path = ROOT / "runs" / "module5-token-budget.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
