"""Run the frozen zero-shot code-review baseline once."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from pydantic import BaseModel

from agents.llm import MODEL, UsageLedger, call_json
from evals.score import score_item

ROOT = Path(__file__).resolve().parents[1]
DATASET_VERSION = "1.1.0"


class Defect(BaseModel):
    category: str
    line: int
    severity: str
    rationale: str


class Review(BaseModel):
    defects: list[Defect]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--effort", default="low")
    args = parser.parse_args()
    prompt = (ROOT / "evals/prompt_baseline.txt").read_text()
    items = [json.loads(line) for line in (ROOT / "evals/dataset.jsonl").read_text().splitlines() if line]
    out_dir = ROOT / "runs/baseline" / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger = UsageLedger(out_dir / "usage.jsonl")
    results, started = [], time.perf_counter()
    for index, item in enumerate(items, 1):
        request = f"{prompt}\n\nFile: {item['file']}\n```python\n{item['input']}\n```"
        item_started = time.perf_counter()
        review, usage = call_json(request, Review, max_tokens=700, effort=args.effort)
        latency = time.perf_counter() - item_started
        ledger.add(usage, label=item["id"], effort=args.effort)
        output = review.model_dump_json()
        scored = score_item(item["expected"], output)
        artifact = {"id": item["id"], "difficulty": item["difficulty"], "file": item["file"],
                    "output": review.model_dump(), "score": scored, "usage": usage.__dict__,
                    "cost_usd": usage.cost_usd, "latency_seconds": latency}
        (out_dir / f"{item['id']}.json").write_text(json.dumps(artifact, indent=2) + "\n")
        results.append(artifact)
        print(f"[{index:02}/{len(items)}] {item['id']} score={scored['score']:.3f} cost=${usage.cost_usd:.4f}")
    elapsed = time.perf_counter() - started
    usage_summary = ledger.summary()
    summary = {"run_id": args.run_id, "dataset_version": DATASET_VERSION, "model": MODEL,
               "effort": args.effort, "items": len(items),
               "mean_score": sum(r["score"]["score"] for r in results) / len(results),
               "per_item_scores": {r["id"]: r["score"]["score"] for r in results},
               **usage_summary, "wall_clock_seconds": elapsed,
               "mean_latency_seconds": sum(r["latency_seconds"] for r in results) / len(results)}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
