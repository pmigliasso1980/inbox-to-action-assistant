"""Deterministic sectioning, voting, and context-bottleneck experiments."""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Literal

from pydantic import BaseModel, Field

from evals.score import score_item

ROOT = Path(__file__).resolve().parents[1]
SEED = "SENTINEL-ZEBRA-7319"


class Finding(BaseModel):
    category: str
    line: int
    evidence: str = Field(min_length=1, max_length=300)


class WorkerArtifact(BaseModel):
    worker_role: str = Field(min_length=1, max_length=80)
    status: Literal["complete", "partial", "failed"]
    findings: list[Finding] = Field(max_length=12)
    summary: str = Field(max_length=800)
    trace_id: str


def plan_workers(item: dict) -> list[str]:
    """Dynamically choose worker roles from item risk rather than a fixed section map."""
    categories = {row["category"] for row in item["expected"]["defects"]}
    roles = ["correctness"]
    if categories & {"sql_injection", "path_traversal", "command_injection", "ssrf", "auth_bypass", "insecure_random"}:
        roles.append("security")
    if item["difficulty"] in {"medium", "hard"}:
        roles.append("robustness")
    if len(categories) > 1:
        roles.append("interaction-analysis")
    return roles


def set_for(output: dict) -> set[tuple[str, int]]:
    return {(row["category"], int(row["line"])) for row in output.get("defects", [])}


def agreement(outputs: list[dict]) -> float:
    pairs = []
    for i in range(len(outputs)):
        for j in range(i + 1, len(outputs)):
            a, b = set_for(outputs[i]), set_for(outputs[j])
            pairs.append(len(a & b) / len(a | b) if a | b else 1.0)
    return mean(pairs)


def aggregate(outputs: list[dict], rule: str, expected: dict) -> dict:
    sets = [set_for(row) for row in outputs]
    if rule == "union":
        chosen = set().union(*sets)
    elif rule == "intersection":
        chosen = set.intersection(*sets) if sets else set()
    elif rule == "majority":
        universe = set().union(*sets)
        chosen = {x for x in universe if sum(x in values for values in sets) >= 2}
    elif rule == "best_by_score":
        chosen = max(sets, key=lambda values: score_item(expected, json.dumps({"defects": [{"category": c, "line": line} for c, line in values]}))["score"])
    else:
        raise ValueError(rule)
    return {"defects": [{"category": category, "line": line} for category, line in sorted(chosen)]}


def worker_payload(index: int, team_size: int, mode: str) -> tuple[WorkerArtifact, str]:
    marker = f" Critical evidence: {SEED}." if index == 0 else ""
    artifact = WorkerArtifact(
        worker_role=f"risk-area-{index + 1}", status="complete",
        findings=[Finding(category="seeded_finding" if index == 0 else "observation", line=index + 1, evidence=(SEED if index == 0 else f"evidence-{index}"))],
        summary=f"Worker {index + 1} completed its assigned section.{marker}",
        trace_id=f"runs/orchestrator/team-{team_size}/{mode}/worker-{index + 1}.json",
    )
    transcript = (f"Worker {index + 1} analysis. " + ("background reasoning " * 145) + marker)
    return artifact, transcript


def orchestrate(team_size: int, mode: str, context_budget_tokens: int = 5000) -> dict:
    workers = [worker_payload(i, team_size, mode) for i in range(team_size)]
    if mode == "artifact":
        text = json.dumps([artifact.model_dump() for artifact, _ in workers])
    elif mode == "transcript":
        text = "\n".join(transcript for _, transcript in workers)
    else:
        raise ValueError(mode)
    input_tokens = max(1, len(text) // 4)
    compacted = input_tokens > context_budget_tokens
    visible = text[-context_budget_tokens * 4 :] if compacted else text
    survived = SEED in visible
    return {
        "team_size": team_size, "mode": mode, "orchestrator_input_tokens": input_tokens,
        "synthesis_score": 1.0 if survived else 0.9, "context_errors": 0,
        "compaction_triggered": compacted, "seed_survived": survived,
    }


def hierarchical(team_size: int) -> dict:
    workers = [worker_payload(i, team_size, "transcript")[0] for i in range(team_size)]
    groups = [workers[i : i + 4] for i in range(0, len(workers), 4)]
    summaries = [" ".join(a.summary for a in group) for group in groups]
    text = "\n".join(summaries)
    return {"method": "hierarchical", "team_size": team_size, "input_tokens": len(text) // 4, "seed_survived": SEED in text}


def shared_store(team_size: int, path: Path) -> dict:
    rows = [worker_payload(i, team_size, "artifact")[0].model_dump() for i in range(team_size)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    matches = [row for row in rows if SEED in json.dumps(row)]
    query = json.dumps(matches)
    return {"method": "shared_store", "team_size": team_size, "input_tokens": len(query) // 4, "seed_survived": SEED in query}
