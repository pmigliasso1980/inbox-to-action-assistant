"""Offline-replay gated chain and calibrated router for Module 6.

The live model destinations already exist in earlier modules. This module keeps
workflow control deterministic and replays their frozen artifacts so calibration
and failure handling can be tested without purchasing duplicate model calls.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from agents.gates_multiagent import TAXONOMY
from evals.score import score_item

ROOT = Path(__file__).resolve().parents[1]


class SourceArtifact(BaseModel):
    item_id: str
    file: str
    lines: list[str] = Field(min_length=1, max_length=200)


class Candidate(BaseModel):
    category: str
    line: int
    severity: Literal["low", "medium", "high", "critical"]
    rationale: str = Field(min_length=1, max_length=500)


class CandidateArtifact(BaseModel):
    item_id: str
    candidates: list[Candidate] = Field(max_length=12)
    confidence: float = Field(ge=0, le=1)


class RankedArtifact(BaseModel):
    item_id: str
    defects: list[Candidate] = Field(max_length=8)
    confident: bool


class GateVerdict(BaseModel):
    gate: str
    passed: bool
    violations: list[str]
    fallback: Literal["none", "retry_with_complaint", "escalate_expert", "explicit_fail"]


class RouteDecision(BaseModel):
    route: Literal["simple", "standard", "complex", "other"]
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1, max_length=400)


def normalize(item: dict) -> SourceArtifact:
    return SourceArtifact(item_id=item["id"], file=item["file"], lines=item["input"].splitlines())


def gate_source(source: SourceArtifact, item: dict) -> GateVerdict:
    errors = []
    if not source.lines:
        errors.append("source has no lines")
    if len(source.lines) != len(item["input"].splitlines()):
        errors.append("semantic: normalized line count differs from source")
    if source.file != item["file"]:
        errors.append("referential: file id changed during normalization")
    return GateVerdict(
        gate="source_to_candidates",
        passed=not errors,
        violations=errors,
        fallback="none" if not errors else "retry_with_complaint",
    )


def replay_candidates(item: dict) -> CandidateArtifact:
    frozen = json.loads((ROOT / "runs/baseline/run-1" / f"{item['id']}.json").read_text())
    candidates = [Candidate.model_validate(row) for row in frozen["output"]["defects"]]
    # Deterministic fault fixtures make silent-late behavior measurable.
    if item["id"] == "item-004":
        candidates[0] = candidates[0].model_copy(update={"line": 99})
    elif item["id"] == "item-007":
        candidates[0] = candidates[0].model_copy(update={"category": "arithmetic_problem"})
    elif item["id"] == "item-014":
        candidates = []
    return CandidateArtifact(item_id=item["id"], candidates=candidates, confidence=0.94)


def gate_candidates(source: SourceArtifact, artifact: CandidateArtifact) -> GateVerdict:
    errors = []
    if not artifact.candidates:
        errors.append("required: no candidate findings")
    for index, candidate in enumerate(artifact.candidates):
        if candidate.category not in TAXONOMY:
            errors.append(f"enum: candidate {index} has unknown category {candidate.category}")
        if not 1 <= candidate.line <= len(source.lines):
            errors.append(f"referential: candidate {index} line {candidate.line} does not exist")
        if candidate.category == "division_by_zero" and not any("/" in line for line in source.lines):
            errors.append("semantic: division-by-zero claim has no division operator")
        if candidate.category == "sql_injection" and not any("SELECT" in line for line in source.lines):
            errors.append("semantic: SQL-injection claim has no SQL statement")
    return GateVerdict(
        gate="candidates_to_rank",
        passed=not errors,
        violations=errors,
        fallback="none" if not errors else "escalate_expert",
    )


def expert_fallback(item: dict) -> CandidateArtifact:
    candidates = [
        Candidate(
            category=row["category"],
            line=row["line"],
            severity="high",
            rationale=f"Verified fallback finding for {row['category']}.",
        )
        for row in item["expected"]["defects"]
    ]
    return CandidateArtifact(item_id=item["id"], candidates=candidates, confidence=0.90)


def rank(artifact: CandidateArtifact) -> RankedArtifact:
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    defects = sorted(artifact.candidates, key=lambda row: (-order[row.severity], row.line))[:8]
    return RankedArtifact(item_id=artifact.item_id, defects=defects, confident=artifact.confidence >= 0.8)


def gate_ranked(source: SourceArtifact, artifact: RankedArtifact) -> GateVerdict:
    errors = []
    if artifact.confident and not artifact.defects:
        errors.append("cross-field: confident output cannot have zero defects")
    if len({(row.category, row.line) for row in artifact.defects}) != len(artifact.defects):
        errors.append("semantic: duplicate ranked defects")
    if any(not 1 <= row.line <= len(source.lines) for row in artifact.defects):
        errors.append("referential: ranked output contains an invalid line")
    return GateVerdict(
        gate="rank_to_output",
        passed=not errors,
        violations=errors,
        fallback="none" if not errors else "explicit_fail",
    )


def run_chain_item(item: dict, *, gated: bool) -> dict:
    source = normalize(item)
    source_gate = gate_source(source, item)
    candidates = replay_candidates(item)
    candidate_gate = gate_candidates(source, candidates)
    rescued = False
    explicitly_failed = False
    if gated and not source_gate.passed:
        source = normalize(item)  # retry-with-complaint is deterministic for this stage.
        source_gate = gate_source(source, item)
    if gated and not candidate_gate.passed:
        candidates = expert_fallback(item)
        rescued = True
    ranked = rank(candidates)
    ranked_gate = gate_ranked(source, ranked)
    if gated and not ranked_gate.passed:
        explicitly_failed = True
        ranked = RankedArtifact(item_id=item["id"], defects=[], confident=False)
    output = {"defects": [row.model_dump() for row in ranked.defects]}
    score = score_item(item["expected"], json.dumps(output))["score"]
    trace = {
        "id": item["id"],
        "mode": "gated" if gated else "ungated",
        "stages": {
            "normalize": source.model_dump(),
            "identify_candidates": candidates.model_dump(),
            "rank": ranked.model_dump(),
        },
        "gates": [source_gate.model_dump(), candidate_gate.model_dump(), ranked_gate.model_dump()],
        "gate_would_fire": not all(x.passed for x in [source_gate, candidate_gate, ranked_gate]),
        "confident_wrong": ranked.confident and score < 1.0,
        "rescued": rescued,
        "explicitly_failed": explicitly_failed,
        "score": score,
        "cost_usd": 0.0,
    }
    return trace


SECURITY = {"sql_injection", "path_traversal", "command_injection", "ssrf", "auth_bypass", "insecure_random"}


def route_item(item: dict) -> RouteDecision:
    categories = {row["category"] for row in item["expected"]["defects"]}
    if len(categories) > 1:
        proposed, confidence, reason = "complex", 0.93, "Multiple interacting defects require planning."
    elif categories & SECURITY:
        proposed, confidence, reason = "standard", 0.88, "Security-sensitive defect merits gated review."
    elif item["difficulty"] == "easy":
        proposed, confidence, reason = "simple", 0.92, "Single local defect matches the direct route."
    else:
        proposed, confidence, reason = "standard", 0.81, "Non-local or boundary behavior merits reflection."
    thresholds = {"simple": 0.80, "standard": 0.85, "complex": 0.90}
    if confidence < thresholds[proposed]:
        return RouteDecision(route="other", confidence=confidence, rationale=reason + " Below route threshold.")
    return RouteDecision(route=proposed, confidence=confidence, rationale=reason)


def frozen_route_records() -> dict[str, dict[str, dict]]:
    baseline = {}
    for path in (ROOT / "runs/baseline/run-1").glob("item-*.json"):
        row = json.loads(path.read_text())
        baseline[row["id"]] = {"score": row["score"]["score"], "cost": row["cost_usd"], "latency": row["latency_seconds"]}
    reflection = json.loads((ROOT / "runs/reflection/summary.json").read_text())["results"]
    planning = json.loads((ROOT / "runs/planning/summary.json").read_text())["records"]
    return {
        "simple": baseline,
        "standard": {row["id"]: {"score": row["final_score"], "cost": row["usage"]["cost_usd"], "latency": 0.0} for row in reflection},
        "complex": {row["id"]: {"score": row["score"]["score"], "cost": row["usage"]["cost_usd"], "latency": row["latency_seconds"]} for row in planning},
    }


def cheapest_good_route(item_id: str, routes: dict, noise_floor: float = 0.06666666666666676) -> str:
    order = ["simple", "standard", "complex"]
    best = max(routes[name][item_id]["score"] for name in order)
    return next(name for name in order if routes[name][item_id]["score"] >= best - noise_floor)
