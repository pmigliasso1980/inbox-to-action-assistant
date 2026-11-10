# Incident Post-Mortem Analyzer

This is the Module 10 capstone: a new, objectively scored task that extracts an
incident's primary cause, severity, remediation owner, remediation, and recurring
pattern. It uses deterministic parsing, a read-only owner directory, strict
result confirmation, and a provenance-enforced graph for cross-session memory.

## Run

Requires Python 3.11+, Pydantic 2, and the repository environment. It makes no
network or model calls.

```bash
python3 capstone_incident/generate_data.py
python3 capstone_incident/run.py
python3 -m pytest -q
```

Configuration is intentionally small: the frozen corpus is in `data/`, the
service ownership directory is `data/owners.json`, and the measured stages are
selected in `run.py`. Outputs are written to `runs/`.

## Final architecture

`input validation → deterministic extraction/reflection → confirmed owner tool
→ provenance graph lookup/write → structured Analysis`

Planning and multi-agent stages are skipped: each incident is independent,
requires no dependency plan, and the measured task has no distinct concurrent
stances that justify extra workers.
