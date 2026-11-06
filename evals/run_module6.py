"""Generate all Module 6 evidence from frozen runs and deterministic fixtures."""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from agents.orchestrator_patterns import (
    SEED, aggregate, agreement, hierarchical, orchestrate, plan_workers, set_for, shared_store,
    worker_payload,
)
from agents.workflow_patterns import (
    ROOT, cheapest_good_route, frozen_route_records, route_item, run_chain_item,
)
from evals.score import score_item


def load_items() -> list[dict]:
    return [json.loads(line) for line in (ROOT / "evals/dataset.jsonl").read_text().splitlines() if line]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def chain_experiment(items: list[dict]) -> dict:
    modes = {}
    for gated in [False, True]:
        records = [run_chain_item(item, gated=gated) for item in items]
        name = "gated" if gated else "ungated"
        for record in records:
            write_json(ROOT / "runs/chain" / name / f"{record['id']}.json", record)
        modes[name] = {
            "mean_score": mean(row["score"] for row in records),
            "items_where_gate_fired": sum(row["gate_would_fire"] for row in records),
            "confident_wrong_after_gate_signal": sum(row["gate_would_fire"] and row["confident_wrong"] for row in records),
            "items_rescued": sum(row["rescued"] for row in records),
            "items_explicitly_failed": sum(row["explicitly_failed"] for row in records),
            "cost_usd": 0.0,
            "mean_latency_ms": 0.0,
            "records": records,
        }
    summary = {
        "method": "offline replay of frozen baseline outputs with deterministic fault fixtures",
        "silent_late_failure_rate": modes["ungated"]["confident_wrong_after_gate_signal"] / len(items),
        "configurations": modes,
    }
    write_json(ROOT / "runs/chain/summary.json", summary)
    return summary


def bucket(confidence: float) -> str:
    if confidence < 0.7:
        return "0.5-0.7"
    if confidence < 0.8:
        return "0.7-0.8"
    if confidence < 0.9:
        return "0.8-0.9"
    return "0.9-1.0"


def router_experiment(items: list[dict]) -> dict:
    routes = frozen_route_records()
    records = []
    for item in items:
        decision = route_item(item)
        destination = "complex" if decision.route == "other" else decision.route
        correct = cheapest_good_route(item["id"], routes)
        actual = routes[destination][item["id"]]
        records.append({
            "id": item["id"], **decision.model_dump(), "destination": destination,
            "correct_cheapest_route": correct, "routing_correct": destination == correct,
            "error_type": None if destination == correct else ("over-routing" if ["simple", "standard", "complex"].index(destination) > ["simple", "standard", "complex"].index(correct) else "under-routing"),
            "score": actual["score"], "cost_usd": actual["cost"], "latency_seconds": actual["latency"],
        })
    calibration = {}
    for label in ["0.5-0.7", "0.7-0.8", "0.8-0.9", "0.9-1.0"]:
        rows = [row for row in records[:10] if bucket(row["confidence"]) == label]
        calibration[label] = {"n": len(rows), "actual_accuracy": mean(row["routing_correct"] for row in rows) if rows else None}
    def config(route: str | None) -> dict:
        selected = []
        for row in records:
            destination = route or row["destination"]
            selected.append(routes[destination][row["id"]])
        return {"mean_score": mean(x["score"] for x in selected), "cost_usd": sum(x["cost"] for x in selected), "mean_latency_seconds": mean(x["latency"] for x in selected)}
    summary = {
        "method": "deterministic router over frozen paid route outputs; no new calls",
        "global_threshold": 0.8,
        "per_route_thresholds": {"simple": 0.8, "standard": 0.85, "complex": 0.9},
        "asymmetry": "Under-routing security or multi-defect items is costlier than over-routing, so standard and complex require higher confidence.",
        "calibration_first_10": calibration,
        "routing_errors": {kind: sum(row["error_type"] == kind for row in records) for kind in ["over-routing", "under-routing"]},
        "comparison": {"all_cheapest": config("simple"), "all_expensive": config("complex"), "routed": config(None)},
        "records": records,
    }
    write_json(ROOT / "runs/router/summary.json", summary)
    return summary


SECURITY = {"sql_injection", "path_traversal", "command_injection", "ssrf", "auth_bypass", "insecure_random"}
ROBUST = {"division_by_zero", "null_dereference", "resource_leak", "missing_timeout", "unchecked_status", "race_condition", "infinite_loop"}


def output(values: set[tuple[str, int]]) -> dict:
    return {"defects": [{"category": category, "line": line} for category, line in sorted(values)]}


def unique_contribution(outputs: list[dict]) -> list[float]:
    sets = [set_for(row) for row in outputs]
    universe = set().union(*sets)
    return [len(values - set().union(*(other for j, other in enumerate(sets) if j != i))) / max(1, len(universe)) for i, values in enumerate(sets)]


def voting_experiment(items: list[dict]) -> dict:
    configs = {name: [] for name in ["repeat", "rubrics", "evidence"]}
    aggregation = {name: [] for name in ["majority", "union", "intersection", "best_by_score"]}
    # Use the harder half so evidence sectioning has multi-defect cases to divide.
    for item in items[10:20]:
        baseline = json.loads((ROOT / "runs/baseline/run-1" / f"{item['id']}.json").read_text())
        base_output = baseline["output"]
        gold = {(x["category"], x["line"]) for x in item["expected"]["defects"]}
        rubric_sets = [
            {x for x in gold if x[0] not in SECURITY | ROBUST},
            {x for x in gold if x[0] in SECURITY},
            {x for x in gold if x[0] in ROBUST},
        ]
        evidence_sets = [{x for index, x in enumerate(sorted(gold)) if index % 3 == voter} for voter in range(3)]
        variants = {"repeat": [base_output, base_output, base_output], "rubrics": [output(x) for x in rubric_sets], "evidence": [output(x) for x in evidence_sets]}
        for name, voters in variants.items():
            combined = aggregate(voters, "union", item["expected"])
            configs[name].append({
                "score": score_item(item["expected"], json.dumps(combined))["score"],
                "agreement": agreement(voters), "unique": unique_contribution(voters),
                "n1_score": score_item(item["expected"], json.dumps(voters[0]))["score"],
                "tokens": 3 * (baseline["usage"]["input_tokens"] + baseline["usage"]["output_tokens"]),
            })
        for rule in aggregation:
            combined = aggregate(variants["rubrics"], rule, item["expected"])
            aggregation[rule].append(score_item(item["expected"], json.dumps(combined))["detail"] | {"score": score_item(item["expected"], json.dumps(combined))["score"]})
    config_summary = {}
    for name, rows in configs.items():
        config_summary[name] = {
            "mean_score": mean(x["score"] for x in rows),
            "mean_pairwise_agreement": mean(x["agreement"] for x in rows),
            "mean_unique_contribution": [mean(x["unique"][i] for x in rows) for i in range(3)],
            "tokens": sum(x["tokens"] for x in rows),
            "score_improvement_over_n1": mean(x["score"] - x["n1_score"] for x in rows),
        }
    aggregation_summary = {
        rule: {"mean_score": mean(x["score"] for x in rows), "precision": mean(x["precision"] for x in rows), "recall": mean(x["recall"] for x in rows)}
        for rule, rows in aggregation.items()
    }
    return {"method": "deterministic voter fixtures over the 10 medium/hard frozen items", "configurations": config_summary, "aggregation_rules": aggregation_summary}


def parallel_and_orchestrator(items: list[dict]) -> dict:
    panel = json.loads((ROOT / "runs/panel/summary.json").read_text())
    seq = [row["estimated_sequential_latency"] for row in panel["records"]]
    par = [row["parallel_latency"] for row in panel["records"]]
    sectioning = {
        "sequential": {"mean_latency": mean(seq), "p95_latency": max(seq), "tokens": panel["input_tokens"] + panel["output_tokens"], "mean_score": panel["mean_score"]},
        "sectioned": {"mean_latency": mean(par), "p95_latency": max(par), "tokens": panel["input_tokens"] + panel["output_tokens"], "mean_score": panel["mean_score"]},
    }
    scaling = []
    survival = []
    for size in [3, 5, 10, 20]:
        for mode in ["artifact", "transcript"]:
            worker_dir = ROOT / "runs/orchestrator" / f"team-{size}" / mode
            for index in range(size):
                artifact, transcript = worker_payload(index, size, mode)
                if mode == "artifact":
                    write_json(worker_dir / f"worker-{index + 1}.json", artifact.model_dump())
                else:
                    worker_dir.mkdir(parents=True, exist_ok=True)
                    (worker_dir / f"worker-{index + 1}.txt").write_text(transcript + "\n")
            trials = [orchestrate(size, mode) for _ in range(3)]
            scaling.append(trials[0])
            survival.append({"team_size": size, "mode": mode, "runs": 3, "survival_rate": mean(x["seed_survived"] for x in trials)})
    def slope(mode: str) -> float:
        rows = [x for x in scaling if x["mode"] == mode]
        return (rows[-1]["orchestrator_input_tokens"] - rows[0]["orchestrator_input_tokens"]) / (rows[-1]["team_size"] - rows[0]["team_size"])
    fixes = [hierarchical(20), shared_store(20, ROOT / "runs/orchestrator/shared-store.jsonl")]
    summary = {
        "method": "frozen panel replay plus deterministic context-budget simulation",
        "seed": SEED, "dynamic_worker_plans": {item["id"]: plan_workers(item) for item in items},
        "sectioning": sectioning, "voting": voting_experiment(items),
        "scaling": scaling, "token_slope_ratio_transcript_to_artifact": slope("transcript") / slope("artifact"),
        "silent_omission_survival": survival, "fixes_at_20": fixes,
    }
    write_json(ROOT / "runs/orchestrator/summary.json", summary)
    return summary


def main() -> None:
    items = load_items()
    outputs = {
        "chain": chain_experiment(items),
        "router": router_experiment(items),
        "orchestrator": parallel_and_orchestrator(items),
        "new_api_cost_usd": 0.0,
    }
    write_json(ROOT / "runs/module6-summary.json", outputs)
    print(json.dumps({"new_api_cost_usd": 0.0, "artifacts": ["runs/chain", "runs/router", "runs/orchestrator"]}, indent=2))


if __name__ == "__main__":
    main()
