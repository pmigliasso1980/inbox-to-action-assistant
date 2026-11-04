# Module 2 submission: Reflection

This is the repository-root grading entry point for Labs 2.1 and 2.2.

## Lab 2.1 deliverables

- [`evals/rubric.md`](evals/rubric.md) — separately committed, immutable rubric with deterministic and subjective criteria.
- [`agents/gates.py`](agents/gates.py) — mechanical validation.
- [`agents/reflection.py`](agents/reflection.py) — structured critique, gate, revision, best-draft selection, and iteration artifacts.
- [`runs/reflection/summary.json`](runs/reflection/summary.json) — 0.9452 reflection score, $0.351780 cost, and full diagnostics.
- [`REFLECTION_REPORT.md`](REFLECTION_REPORT.md) — no demonstrated lift beyond the 0.0667 noise floor.

## Lab 2.2 deliverables

- [`FAILURE_INJECTION_PREDICTIONS.md`](FAILURE_INJECTION_PREDICTIONS.md) — predictions written before running.
- Five run directories: `runs/reflection-control`, `runs/reflection-inject-self-confirm`, `runs/reflection-inject-drift`, `runs/reflection-inject-nonmono`, and `runs/reflection-all-controls`.
- [`FAILURE_INJECTION_REPORT.md`](FAILURE_INJECTION_REPORT.md) — comparative table, evidence quotes, conclusions, and three production alerts.

The same 10-item subset was used for all five Lab 2.2 configurations. Rubric drift caused the largest score loss; self-confirmation caused the largest cost increase; forced non-monotonic revision did not reduce score on the saturated subset.

## Archived Module 1 summary

## Lab 1.1 deliverables

- [`agents/llm.py`](agents/llm.py) — shared `claude-opus-5` client, structured output, token counting, normalized usage, cost accounting, retry configuration, and JSONL usage logging.
- [`verify_setup.py`](verify_setup.py) — token count plus low/high effort round trip.
- [`SETUP_BASELINE_NOTE.md`](SETUP_BASELINE_NOTE.md) — 16-line usage and cost comparison.
- [`PROJECT_TREE.txt`](PROJECT_TREE.txt) — directory listing proving `agents/`, `evals/`, `data/`, `runs/`, and `graph/` exist.

Observed setup result: both low and high effort used 23 input and 116 output tokens and cost **$0.003015 each**. High effort was not materially better for the trivial prompt.

## Lab 1.2 deliverables

- [`evals/dataset.jsonl`](evals/dataset.jsonl) — 20 frozen measurement items, version 1.1.0.
- [`evals/devset.jsonl`](evals/devset.jsonl) — 5 separate prompt-development items.
- [`evals/prompt_baseline.txt`](evals/prompt_baseline.txt) — frozen zero-shot prompt and defect taxonomy.
- [`evals/score.py`](evals/score.py) — deterministic exact category-and-line precision, recall, and F1.
- [`evals/run_baseline.py`](evals/run_baseline.py) — one-call-per-item harness with raw artifacts, usage, cost, and latency.
- [`runs/baseline/run-1/summary.json`](runs/baseline/run-1/summary.json) — mean score **0.8786**, cost **$0.144060**.
- [`runs/baseline/run-2/summary.json`](runs/baseline/run-2/summary.json) — mean score **0.9452**, cost **$0.144585**.
- [`BASELINE_REPORT.md`](BASELINE_REPORT.md) — task justification, **0.0667 noise floor**, cost/latency, five failure classifications, and architectural roadmap.

All 40 official raw item outputs are committed under `runs/baseline/`. No model judge was used. The initial taxonomy calibration is preserved separately under `runs/calibration-taxonomy-v1/` rather than being presented as a valid baseline.

## Archived earlier submissions

- [`TOKEN_BILL_LAB_NOTES.md`](TOKEN_BILL_LAB_NOTES.md) — Read Your Token Bill.
- [`MCP_CLIENT_LAB_NOTES.md`](MCP_CLIENT_LAB_NOTES.md) — MCP client lab.
