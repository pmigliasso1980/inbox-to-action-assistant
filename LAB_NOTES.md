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

# Module 5 submission: Multi-agent collaboration

## Lab 5.1 — Generator–critic

- `agents/gen_critic.py` implements isolated role handoffs, prompt caching, best-artifact selection,
  and a maximum of three iterations.
- `agents/gates_multiagent.py` defines bounded Pydantic contracts, reference checks, and decision
  invariants with one-retry escalation.
- `runs/gen-critic/summary.json` and `runs/gen-critic-neutral/summary.json` contain the adversarial and
  stance-ablation measurements.
- `GEN_CRITIC_REPORT.md` provides the Module 2 comparison and deployment verdict.

## Lab 5.2 — Parallel panel

- `agents/panel.py` runs correctness, security, and robustness reviewers concurrently and merges their
  issues deterministically with provenance.
- `evals/panel_distinctness.json` freezes thresholds and pairwise distinctness examples before runs.
- `runs/panel/summary.json` contains overlap, unique-contribution, role-ablation, cost, and latency data.
- `runs/module5-token-budget.json` compares four architectures by measured tokens rather than agents.
- `PANEL_REPORT.md` records the echo-chamber result, formal keep/drop decisions, and recommendation.

The cost-controlled experiment used three fixed items. All configurations scored 1.0, so the evidence
supports a single combined critic rather than a permanent three-role panel. Actual new Anthropic spend
was **$0.570675**, including the smoke test, versus the authorized **$3.00** ceiling.

# Module 6 submission: Workflow patterns

- `agents/workflow_patterns.py` — typed three-stage chain, semantic gates, three fallback strategies,
  constrained four-route classifier, asymmetric thresholds, and frozen-route evaluation.
- `runs/chain/summary.json` — 20-item gated/ungated comparison and full per-item traces.
- `runs/router/summary.json` — 10-item calibration table plus 20-item score/cost/latency comparison.
- `WORKFLOW_PATTERNS_REPORT.md` — silent-late failure example, caching observation, and router verdict.
- `agents/orchestrator_patterns.py` — dynamic worker planning, sectioning/voting utilities, both handoff
  modes, hierarchical synthesis, and file-backed shared store.
- `runs/orchestrator/summary.json` — sectioning, three voting configurations, aggregation rules,
  3/5/10/20-worker scaling, and three-run seed survival.
- `PARALLEL_ORCHESTRATOR_REPORT.md` — measured bottleneck and graph-transition argument.

Module 6 deliberately replays already-paid model artifacts and uses deterministic fault/context
fixtures. All new measurements are reproducible offline; **new API spend was $0.00**.
