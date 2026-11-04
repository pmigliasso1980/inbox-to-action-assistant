# Module 1 submission: Architecture Over Model

This is the repository-root grading entry point for Labs 1.1 and 1.2.

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
