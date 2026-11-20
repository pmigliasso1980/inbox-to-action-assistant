# Reports and Evidence

## Authority and provenance

Files explicitly marked “generated” must be changed through their generating
script. JSON and JSONL under `runs/` are machine-readable evidence; Markdown
reports interpret that evidence and must distinguish observations from
projections.

## Refresh order

```bash
python3 evals/run_module10.py
python3 reports/cost_model.py
python3 reports/monitors.py
python3 reports/generate_dashboard.py
python3 reports/generate_effort_sweep.py
```

Then verify:

```bash
python3 -m pytest -q graph/test_module10.py
git diff --check
```

## Key outputs

- `dashboard.md`: score, cost, latency, cache, errors, and Rule 5 panels.
- `cost_model.md` / `.json`: component, item, marginal, and cost-per-point data.
- `monitors.json`: five silent-failure monitors and their latest verdicts.
- `READINESS_AUDIT.md`: checklist, reliability trace, cache audit, and limits.
- `runs/calls.jsonl`: normalized call records with cached tokens separated.
- `runs/graph_ops.jsonl`: graph reads/writes including cross-session status.

## Interpretation rules

- Do not divide cost by a score delta inside the noise floor.
- Do not compare stages with different evaluation scopes as if paired.
- Report missing latency as “not retained,” not zero.
- A projected cache saving is not an observed saving.
- A graph type with near-zero reads and one reader fails Rule 5.
