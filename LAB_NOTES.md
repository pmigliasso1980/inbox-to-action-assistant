# Module 3 submission: Tool Use

This is the repository-root grading index for Labs 3.1 and 3.2.

## Lab 3.1 — Build a Tool-Using Agent

- [`agents/tool_agent.py`](agents/tool_agent.py) — hand-written loop, parallel results, `pause_turn`, cap handling, explicit errors, and traces.
- [`agents/review_tools.py`](agents/review_tools.py) — three strict, read-only tools with executor validation and result confirmation.
- [`evals/run_tools.py`](evals/run_tools.py) — fixed 20-item tools-in-evaluation harness.
- [`runs/tools/summary.json`](runs/tools/summary.json) — score, deltas, tool/error/rejection metrics, tokens, cost, and latency.
- [`runs/tools/item-001/trace.jsonl`](runs/tools/item-001/trace.jsonl) — complete end-to-end trace.
- [`TOOLS_REPORT.md`](TOOLS_REPORT.md) — progression, rationale, failure mapping, confirmation evidence, and cost comparison.

Observed result: mean F1 **0.8833**, only +0.0048 over baseline and -0.0619 versus reflection, below the 0.0667 noise floor. Cost was **$0.669085**. This generic tool set did not produce reliable lift.

## Lab 3.2 — Fallbacks and Permission Boundaries

- [`agents/tool_controls.py`](agents/tool_controls.py) — six failure modes, retry/fallback policy, separate handles, strict write schema, approval callback, dry run, validation, and auditing.
- [`evals/run_fallbacks.py`](evals/run_fallbacks.py) — 120-item implicit/explicit failure matrix.
- [`runs/fallbacks/summary.json`](runs/fallbacks/summary.json) — all 12 configuration summaries.
- [`evals/run_boundary_cases.py`](evals/run_boundary_cases.py) — reproducible four-case boundary proof.
- [`runs/audit.jsonl`](runs/audit.jsonl) and [`runs/boundary-cases.json`](runs/boundary-cases.json) — approved, denied, invalid, and hostile attempts.
- [`FALLBACK_PERMISSION_REPORT.md`](FALLBACK_PERMISSION_REPORT.md) — recovery analysis, boundary results, and junior-engineer analogy.

Explicit fallback invocation reached 100% for rate-limit, timeout, auth, and empty modes. The measured ungrounded-answer rate was **0%** in every configuration. Matrix cost was **$2.768370**.

## Verification and spend

```bash
PYTHONPATH=. pytest -q
PYTHONPATH=. python3 evals/run_boundary_cases.py
```

All **45 tests pass**. Total new Anthropic spend for Module 3 was **$3.437455**, below the authorized $8 ceiling.

Earlier submissions remain in their dedicated reports, including `BASELINE_REPORT.md`, `REFLECTION_REPORT.md`, and `FAILURE_INJECTION_REPORT.md`.
