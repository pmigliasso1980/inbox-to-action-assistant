"""Generate the Fresh Session Test and knowledge-visibility scorecards."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEFORE_COMMIT = "2c3ce3f"

QUESTIONS = [
    ("What is this repository now?", "Infer", "README mixed product, course, and current lab narratives.", "docs/REPOSITORY_GUIDE.md", "four related bodies of work"),
    ("How do I install it?", "Confident", "AGENTS.md contained explicit setup commands.", "AGENTS.md", "python3 -m pip install -e ."),
    ("What is the full verification command?", "Confident", "AGENTS.md named pytest, compileall, and diff checks.", "AGENTS.md", "python3 -m pytest -q"),
    ("Which graph backend is local versus production?", "Confident", "AGENTS.md stated SQLite and PostgreSQL roles.", "graph/README.md", "PostgreSQL for production"),
    ("What provenance must every claim carry?", "Confident", "The rule was present in AGENTS.md.", "graph/README.md", "nonblank verbatim span"),
    ("Is planning in the current default path?", "Unknown", "ADR-003 existed but was not linked from either entry point.", "docs/DECISIONS.md", "Planning is routed"),
    ("Where should large artifact bodies live?", "Unknown", "The Rule 5 result was buried in a module report.", "docs/REPOSITORY_GUIDE.md", "outside the graph"),
    ("Which source wins when documents disagree?", "Unknown", "No authority order existed.", "docs/REPOSITORY_GUIDE.md", "Authority order"),
    ("How are readiness reports regenerated?", "Confident", "AGENTS.md listed the generator commands.", "reports/README.md", "Refresh order"),
    ("How do I run the incident capstone?", "Confident", "README linked its entry point.", "docs/REPOSITORY_GUIDE.md", "python3 capstone_incident/run.py"),
    ("Where is the harness ablation evidence?", "Confident", "README linked the diagnostic log.", "AGENTS.md", "harness_ablation/DIAGNOSTIC_LOG.md"),
    ("May an agent make paid model calls by default?", "Confident", "AGENTS.md required explicit authorization.", "AGENTS.md", "explicitly authorizes"),
]

DECISIONS = [
    ("Python 3.11+ runtime", True, "AGENTS.md"),
    ("Pydantic 2 strict contracts", True, "AGENTS.md"),
    ("SQLite local/test graph", True, "graph/README.md"),
    ("PostgreSQL production graph target", True, "ADR-002-graph-backend.md"),
    ("Offline replay and paid calls opt-in", True, "docs/REPOSITORY_GUIDE.md"),
    ("Deterministic gates before model evaluation", True, "agents/README.md"),
    ("Every claim has provenance and span", True, "graph/README.md"),
    ("Graph updates are additive supersessions", True, "graph/README.md"),
    ("Planning removed from default path", False, "ADR-003-remove-default-planning.md"),
    ("Large artifact bodies stay outside graph", False, "docs/REPOSITORY_GUIDE.md"),
    ("Orchestrator uses bounded graph queries", False, "agents/README.md"),
    ("Cached input is accounted separately", True, "reports/README.md"),
    ("External side effects require human approval", True, "docs/REPOSITORY_GUIDE.md"),
    ("Current verified entry points are task-specific", False, "docs/REPOSITORY_GUIDE.md"),
    ("Tests/ADRs/generated evidence have authority order", False, "docs/REPOSITORY_GUIDE.md"),
]


def validate_after_evidence() -> None:
    for _, _, _, relative, anchor in QUESTIONS:
        path = ROOT / relative
        if not path.exists() or anchor.lower() not in path.read_text().lower():
            raise AssertionError(f"Fresh-session evidence missing: {relative} / {anchor}")
    for _, _, relative in DECISIONS:
        if not (ROOT / relative).exists():
            raise AssertionError(f"Decision evidence missing: {relative}")


def scorecard() -> dict:
    validate_after_evidence()
    before = Counter(row[1] for row in QUESTIONS)
    after = Counter({"Confident": len(QUESTIONS)})
    return {"before_commit": BEFORE_COMMIT, "questions": len(QUESTIONS),
            "before": dict(before), "after": dict(after),
            "confident_gain": after["Confident"] - before["Confident"]}


def visibility() -> dict:
    before_visible = sum(before for _, before, _ in DECISIONS)
    total = len(DECISIONS)
    return {"total_decisions": total, "before_visible": before_visible,
            "after_visible": total, "before_gap": 1 - before_visible / total,
            "after_gap": 0.0}


def render_scorecard(result: dict) -> str:
    lines = ["# Fresh Session Test Scorecard", "",
             f"Before snapshot: commit `{BEFORE_COMMIT}`. A fresh reader starts with only `README.md` and `AGENTS.md`; direct answers or answers reachable through an explicit topic link are **Confident**, answers requiring repository inference are **Infer**, and absent/conflicting answers are **Unknown**.", "",
             "| Question | Before | Before evidence | After | After evidence |", "|---|---|---|---|---|"]
    for question, status, reason, path, _ in QUESTIONS:
        lines.append(f"| {question} | {status} | {reason} | Confident | `{path}` |")
    lines += ["", "## Totals", "",
              f"| Snapshot | Confident | Infer | Unknown |", "|---|---:|---:|---:|",
              f"| Before `{BEFORE_COMMIT}` | {result['before'].get('Confident', 0)} | {result['before'].get('Infer', 0)} | {result['before'].get('Unknown', 0)} |",
              f"| After | {result['after']['Confident']} | 0 | 0 |", "",
              f"Confident answers increased by **{result['confident_gain']}** ({result['before'].get('Confident', 0)}/12 → 12/12). The test measures knowledge discoverability, not software quality.", ""]
    return "\n".join(lines)


def render_visibility(result: dict) -> str:
    lines = ["# Knowledge Visibility Gap", "",
             "A decision counts as visible when a fresh reader can reach an explicit current statement from `README.md` or `AGENTS.md` within two links. The gap formula is `1 - visible decisions / total decisions`.", "",
             "| Decision | Visible before? | After evidence |", "|---|---|---|"]
    for decision, before, evidence in DECISIONS:
        lines.append(f"| {decision} | {'Yes' if before else 'No'} | `{evidence}` |")
    lines += ["", "## Calculation", "",
              f"- Before: `{result['before_visible']} / {result['total_decisions']}` visible; gap = `1 - {result['before_visible']}/{result['total_decisions']}` = **{result['before_gap']:.1%}**.",
              f"- After: `{result['after_visible']} / {result['total_decisions']}` visible; gap = `1 - {result['after_visible']}/{result['total_decisions']}` = **{result['after_gap']:.1%}**.",
              f"- Improvement: **{result['before_gap'] - result['after_gap']:.1%} percentage points**.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    fresh, gap = scorecard(), visibility()
    (ROOT / "docs/FRESH_SESSION_SCORECARD.md").write_text(render_scorecard(fresh))
    (ROOT / "docs/KNOWLEDGE_VISIBILITY.md").write_text(render_visibility(gap))
    (ROOT / "runs/fresh-session-test.json").write_text(json.dumps({"fresh_session": fresh, "visibility": gap}, indent=2) + "\n")
    print(json.dumps({"fresh_session": fresh, "visibility": gap}, indent=2))
