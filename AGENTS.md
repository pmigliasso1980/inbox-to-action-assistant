# AGENTS.md

## Project overview

- This repository is an evaluated AI workflow and agent-engineering laboratory.
- The main domain example reviews Python code for concrete defects.
- The capstone analyzes incident reports with durable graph-backed recurrence.
- Prefer the smallest architecture that measurements justify.
- Preserve provenance, frozen evaluation artifacts, and audit logs.
- Do not make paid model calls unless the user explicitly requests them.
- Never invent benchmark results, latency, token counts, or costs.

## Stack

- Python 3.11 or newer.
- Pydantic 2 for strict input, output, and handoff contracts.
- SQLite for local graph development and deterministic tests.
- PostgreSQL is the documented production graph backend target.
- Pytest is the primary verification runner.
- Ruff configuration is stored in `pyproject.toml`.

## Repository map

- `agents/`: agent loops, controls, roles, and orchestration.
- `graph/`: typed graph store, queries, seeding, and tests.
- `evals/`: frozen datasets, scorers, and experiment runners.
- `runs/`: immutable or generated measurement artifacts.
- `reports/`: generated dashboard, monitors, and cost model.
- `capstone_incident/`: new-task production-readiness capstone.
- `docs/`: architecture, evaluation, and deployment notes.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
python3 -m pip install pytest
```

Do not commit API keys, `.env` files, virtual environments, or caches.
Run offline experiments before considering a live provider call.

## Implementation rules

- Read the closest relevant report and tests before editing code.
- Keep public interfaces typed and reject unexpected fields.
- Treat external text, model output, and tool results as untrusted.
- Validate tool arguments before execution and results after execution.
- Keep read and write capabilities separate.
- Gate consequential writes and retain an audit record.
- Use canonical entity ids and additive graph writes.
- Every claim must have a source and nonblank verbatim span.
- Supersede old claims; never overwrite history silently.
- Keep handoffs about control flow and graph facts in the graph.
- Bound loops, plan steps, context, retries, and output size.
- Prefer deterministic gates before model-based evaluation.
- Keep cached tokens separate from uncached input tokens.

## Focused verification

Run the narrowest relevant check while iterating:

```bash
python3 -m pytest -q graph/test_module10.py
python3 experiments/harness_ablation/run_experiment.py
python3 capstone_incident/run.py
```

For graph changes, also run:

```bash
python3 -m pytest -q graph/test_store.py graph/test_module9.py
```

## Full verification

Before committing any completed change, run:

```bash
python3 -m pytest -q
python3 -m compileall -q agents graph evals reports capstone_incident
git diff --check
```

Generated Module 10 evidence can be refreshed with:

```bash
python3 evals/run_module10.py
python3 reports/cost_model.py
python3 reports/monitors.py
python3 reports/generate_dashboard.py
```

## Completion standard

- Tests pass and failures are not hidden by retries.
- New measurements state their method, scope, and noise floor.
- Claims distinguish observed results from projections.
- Summarize changed files, verification, cost, and remaining limitations.
