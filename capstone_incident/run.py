"""Run every measured capstone stage and generate immutable JSON evidence."""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from capstone_incident.scorer import score
from capstone_incident.system import PatternGraph, analyze

CAP = Path(__file__).resolve().parent


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(p * len(ordered)))]


def run_stage(items: list[dict], stage: str, variant: int = 1) -> tuple[dict, PatternGraph, list[dict]]:
    graph, records, latencies = PatternGraph(), [], []
    for index, item in enumerate(items):
        started = time.perf_counter()
        output = analyze(item["id"], item["input"], graph, stage=stage, run_variant=variant,
                         session=f"session-{1 + index // 10}")
        latency = (time.perf_counter() - started) * 1000
        latencies.append(latency)
        records.append({"id": item["id"], "partition": item["partition"],
                        "output": output.model_dump(), "score": score(item["expected"], output.model_dump()),
                        "latency_ms": latency})
    summary = {"stage": stage, "variant": variant, "items": len(records),
               "mean_score": statistics.mean(x["score"]["score"] for x in records),
               "p50_latency_ms": statistics.median(latencies), "p95_latency_ms": percentile(latencies, .95),
               "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
               "mean_first_encounter": statistics.mean(x["score"]["score"] for x in records if x["partition"] == "first-encounter"),
               "mean_repeat_pattern": statistics.mean(x["score"]["score"] for x in records if x["partition"] == "repeat-pattern")}
    return summary, graph, records


def main() -> None:
    items = [json.loads(line) for line in (CAP / "data/eval.jsonl").read_text().splitlines()]
    output_dir = CAP / "runs"
    output_dir.mkdir(exist_ok=True)
    all_summaries, all_records, graph_ops = [], {}, []
    for label, stage, variant in [("baseline-1", "baseline", 1), ("baseline-2", "baseline", 2),
                                  ("reflection", "reflection", 1), ("tools", "tools", 1),
                                  ("graph", "graph", 1)]:
        summary, graph, records = run_stage(items, stage, variant)
        summary["label"] = label
        all_summaries.append(summary)
        all_records[label] = records
        if label == "graph":
            graph_ops = graph.operations
        (output_dir / f"{label}.json").write_text(json.dumps({"summary": summary, "records": records}, indent=2) + "\n")
    noise = abs(all_summaries[0]["mean_score"] - all_summaries[1]["mean_score"])
    result = {"task": "incident post-mortem analyzer", "noise_floor": noise,
              "stages": all_summaries, "graph_ops": graph_ops, "new_api_cost_usd": 0.0}
    (output_dir / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    (output_dir / "graph_ops.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in graph_ops))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
