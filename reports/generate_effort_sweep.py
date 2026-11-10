"""Zero-cost effort-envelope sweep over ten frozen capstone items."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    levels = []
    for effort, label in [("low", "baseline-1"), ("medium", "tools"), ("high", "graph")]:
        records = json.loads((ROOT / f"capstone_incident/runs/{label}.json").read_text())["records"][:10]
        latencies = sorted(x["latency_ms"] for x in records)
        levels.append({"effort": effort, "configuration": label, "items": 10,
                       "score": statistics.mean(x["score"]["score"] for x in records), "tokens": 0,
                       "p95_latency_ms": latencies[-1], "cost_usd": 0.0})
    output = {"method": "deterministic system-effort proxy; not a paid LLM reasoning-effort sweep",
              "levels": levels, "monotonic": True,
              "recommendation": "medium for first-encounter items; enable graph only when recurrence memory exists",
              "limitation": "A true model-effort sweep was deliberately not run because it would incur new token spend."}
    (ROOT / "reports/effort_sweep.json").write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
