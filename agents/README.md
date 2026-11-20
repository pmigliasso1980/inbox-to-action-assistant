# Agent Layer

## Purpose

`agents/` contains reusable loops and controls rather than a permanent team of
autonomous workers. Select a pattern only when measured failures justify it.

## Control flow

1. Deterministic gates reject mechanically invalid work.
2. A bounded worker produces a typed artifact.
3. Tools validate arguments and confirm results.
4. Graph-aware components query only their declared read scope.
5. Durable findings are written with provenance and role metadata.
6. The orchestrator synthesizes from bounded queries, not worker transcripts.

`graph_roles.py` is the executable role registry. `graph_orchestrator.py` holds
typed handoffs and the concurrent-read/serialized-write policy. Role prompts are
under `agents/roles/`.

## Hard boundaries

- Handoffs carry assignments, completion criteria, status, and graph ids.
- Facts intended to survive the run belong in the graph.
- A role attempting an out-of-scope write must raise and log the violation.
- Historian is read-only.
- Entity writes are canonical and idempotent.
- Candidate claims append; tech lead serializes supersession.

## Verification

```bash
python3 -m pytest -q graph/test_module9.py graph/test_module10.py
python3 evals/run_module9.py
```

The measured graph context slope, role traces, and Rule 5 audit are stored in
`runs/graph-orchestrator-summary.json` and summarized in `MODULE_9_REPORT.md`.
