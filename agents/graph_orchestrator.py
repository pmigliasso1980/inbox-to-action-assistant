"""Graph-orchestrated replay: typed handoffs, bounded synthesis, observable roles."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from agents.graph_roles import ROLES, ScopedGraph
from graph.store import GraphStore, SourceRef


class WorkAssignment(BaseModel):
    run_id: str
    entity_id: str
    role: Literal["architect", "tech_lead", "developer", "historian"]
    completion_criterion: str = Field(min_length=5)


class RoleCompletion(BaseModel):
    run_id: str
    role: str
    status: Literal["complete", "blocked"]
    graph_write_ids: list[str]


class GraphOrchestrator:
    """Workers query independently; only completion/control metadata returns in handoffs."""
    def __init__(self, graph_path: str | Path):
        self.graph_path = str(graph_path)
        self.trace: list[dict] = []

    def _read_worker(self, assignment: WorkAssignment) -> RoleCompletion:
        started = time.perf_counter()
        store = GraphStore(self.graph_path)
        query = ROLES[assignment.role].read_scope
        rows = query(store, assignment.entity_id)
        store.close()
        event = {
            "role": assignment.role, "query": query.__name__, "result_size": len(rows),
            "writes": [], "tokens": 0, "cost_usd": 0.0,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        }
        self.trace.append(event)
        return RoleCompletion(run_id=assignment.run_id, role=assignment.role, status="complete", graph_write_ids=[])

    def dispatch(self, assignments: list[WorkAssignment]) -> list[RoleCompletion]:
        with ThreadPoolExecutor(max_workers=min(4, len(assignments))) as pool:
            completions = list(pool.map(self._read_worker, assignments))
        # Independent discovery reads are concurrent. Durable writes are then
        # serialized to make supersede/version ordering deterministic.
        store = GraphStore(self.graph_path)
        run_id = assignments[0].run_id
        if store.get_node(run_id) is None:
            store.write_node("Run", {
                "id": run_id, "started_at": "2026-11-05T19:00:00Z",
                "model": "offline-graph-replay", "effort": "none",
                "prompt_version": "module9-role-prompts-v1", "dataset_version": "1.1.0",
                "created_by_role": "orchestrator",
            })
        for assignment, completion in zip(assignments, completions):
            scoped = ScopedGraph(store, assignment.role)
            written: list[str] = []
            if assignment.role in {"architect", "developer"}:
                artifact_id = f"artifact-{assignment.run_id}-{assignment.role}"
                written.append(scoped.write_artifact({
                    "id": artifact_id, "kind": f"{assignment.role}_output",
                    "content_ref": f"runs/module9/{assignment.run_id}/{assignment.role}.json",
                    "created_by_run": run_id, "created_by_role": assignment.role,
                }, "source-001"))
            elif assignment.role == "tech_lead":
                written.append(scoped.write_claim(
                    statement="The Module 9 review stage completed with graph-backed evidence.",
                    sources=[SourceRef(source_id="source-001", span="graph-backed review completion")],
                    confidence=.9, run_id=run_id, mentions=[assignment.entity_id],
                    subject=assignment.entity_id, predicate="review_completed", object="true",
                ))
            completion.graph_write_ids.extend(written)
            event = next(x for x in self.trace if x["role"] == assignment.role)
            event["writes"] = written
        store.close()
        return completions

    def synthesize(self, entity_id: str) -> dict:
        store = GraphStore(self.graph_path)
        findings = ROLES["tech_lead"].read_scope(store, entity_id)
        store.close()
        # Bounded query result, independent of worker/transcript count.
        findings = findings[:3]
        return {"query": "tech_lead_read(limit=3)", "finding_ids": [x.id for x in findings]}


# Concurrent supersede policy: canonical entity upserts are idempotent. Workers may
# only append candidate claims; the tech lead serializes supersedes after comparing
# current claim ids, so two workers cannot silently replace the same version.
