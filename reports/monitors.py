"""Five silent-failure monitors suitable for CI."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graph.store import GraphStore


def run_monitors() -> list[dict]:
    store = GraphStore(ROOT / "graph/knowledge.db")
    no_source = [x.id for x in store.nodes("Claim") if not store.provenance_edges(x.id)]
    store.close()
    m9 = json.loads((ROOT / "runs/graph-orchestrator-summary.json").read_text())
    graph_slope = m9["token_slopes_per_worker"]["graph"]
    # Tool traces record confirmed and rejected calls; the injected fallback
    # suite supplies rejection coverage even when the normal corpus is clean.
    fallback = json.loads((ROOT / "runs/fallbacks/summary.json").read_text()) if (ROOT / "runs/fallbacks/summary.json").exists() else {}
    injected = [x for x in fallback.get("configurations", []) if x["failure_mode"] != "none"]
    rejection_rate = sum(x["fallback_invocation_rate"] for x in injected) / max(1, len(injected))
    executions: list[tuple[str, int, str]] = []
    for trace in (ROOT / "runs/planning").glob("item-*/trace.jsonl"):
        for event in map(json.loads, trace.read_text().splitlines()):
            if event.get("event") == "step":
                executions.append((trace.parent.name, event["plan"], event["artifact"]["step_id"]))
    duplicate_count = len(executions) - len(set(executions))
    artifact_count = sum(len(x["writes"]) for x in m9["role_trace"])
    results = [
        {"monitor": "claims_without_source", "value": len(no_source), "threshold": "== 0", "ok": len(no_source) == 0,
         "response": "Block deployment; restore a supports/derived_from edge with a verbatim span."},
        {"monitor": "duplicated_step_executions", "value": duplicate_count, "threshold": "== 0", "ok": duplicate_count == 0,
         "response": "Stop the run; inspect idempotency keys and resume from the last unique artifact."},
        {"monitor": "orchestrator_token_slope", "value": graph_slope, "threshold": "<= 1 token/worker and non-increasing", "ok": graph_slope <= 1,
         "response": "Reject the change; replace forwarded transcripts with a bounded graph query."},
        {"monitor": "confirmation_rejection_rate", "value": rejection_rate, "threshold": "> 0 in injected suite", "ok": rejection_rate > 0,
         "response": "Disable write tools and restore result-confirmation checks."},
        {"monitor": "artifacts_written_per_run", "value": artifact_count, "threshold": ">= 3 for Module 9 orchestration", "ok": artifact_count >= 3,
         "response": "Treat telemetry as broken; block release until expected artifacts are present."},
    ]
    return results


if __name__ == "__main__":
    output = {"monitors": run_monitors()}
    (ROOT / "reports/monitors.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
