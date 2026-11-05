# Module 4 submission: Planning

This repository-root index covers Labs 4.1 and 4.2.

## Lab 4.1 — Validated planning agent

- [`evals/planning_candidates.json`](evals/planning_candidates.json) — five candidates frozen before measurement.
- [`agents/plan_validator.py`](agents/plan_validator.py) — structured schema, all seven validation checks, and DAG ordering.
- [`agents/planner.py`](agents/planner.py) — bounded artifacts, tool-step execution, success criteria, preserving replans, two-strikes escalation, caching, and budgets.
- [`evals/run_planning.py`](evals/run_planning.py) — full-set and cache-ablation harness.
- [`runs/planning/summary.json`](runs/planning/summary.json) — complete quality, plan-health, token, cost, cache, and latency metrics.
- [`runs/planning/item-006/trace.jsonl`](runs/planning/item-006/trace.jsonl) — full plan → criterion failure → preserving replan → synthesis trace.
- [`PLANNING_REPORT.md`](PLANNING_REPORT.md) — candidate definition, metrics, cost engineering, and verdict.

Planning produced **0.8436 mean F1**, **0.5476 candidate F1**, and cost **$1.273165**, or **8.84× baseline**. It did not beat the 0.0667 noise floor. Prompt caching was verified with 48,024 cache-read tokens and saved 34.72% on the five-item cost comparison.

## Lab 4.2 — Replanning under failure

- [`evals/run_replanning_experiments.py`](evals/run_replanning_experiments.py) — switchable naive/preserving variants and thresholds 1/2/3/5.
- [`evals/summarize_module4.py`](evals/summarize_module4.py) — offline consolidation of valid controlled runs.
- [`runs/replanning/summary.json`](runs/replanning/summary.json) — Part 1 comparison, threshold sweep, and five escalation assessments.
- [`REPLANNING_REPORT.md`](REPLANNING_REPORT.md) — duplication, cost, side effects, side-by-side plan analysis, threshold recommendation, and escalation quality.

Preserving results eliminated measured duplicates (1 → 0) and raised mean F1 from 0.6143 to 0.6810, although it cost more in this sample. No transient success required a third attempt; threshold 2 recovered both transient cases and is the recommended knee.

## Verification and actual spend

```bash
PYTHONPATH=. pytest -q
PYTHONPATH=. python3 evals/summarize_module4.py
```

All **51 tests pass**. Actual Module 4 Anthropic spend, including smoke/calibration and interrupted controls, was **$6.289885**, below the authorized $18 ceiling. Only valid controlled artifacts are included in the submission.

Earlier modules remain available in `BASELINE_REPORT.md`, `REFLECTION_REPORT.md`, `FAILURE_INJECTION_REPORT.md`, `TOOLS_REPORT.md`, and `FALLBACK_PERMISSION_REPORT.md`.
