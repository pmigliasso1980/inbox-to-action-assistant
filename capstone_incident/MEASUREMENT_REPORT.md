# Capstone Measurement Report

## Evaluation design

The frozen evaluation set contains 20 incidents: ten first encounters followed
by ten repeat-pattern incidents. It covers ten services and ten ownership
relationships. Five deliberately demanding remediation cases require a
service-specific validation step. A separate five-item devset was generated
before the evaluated runs and is not included in scores.

`scorer.py` performs exact matching over five output fields. There is no model
judge, so judge agreement is not applicable. The zero-shot prompt equivalent is
frozen in the baseline implementation: classify cause and severity from the
report without tools or accumulated state.

Two baseline runs score 0.50 and 0.48, producing a **0.02 noise floor**. The
second run preserves one observed boundary instability rather than pretending
that deterministic replay has zero uncertainty.

## Progression

| Stage | Score | Δ | Cost/item | p50 ms | p95 ms | Tokens | Cost/point |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.50 | — | $0 | local | <1 | 0 | — |
| + reflection/rubric repair | 0.65 | +0.15 | $0 | local | <1 | 0 | $0 |
| + confirmed owner tool | 0.85 | +0.20 | $0 | local | <1 | 0 | $0 |
| + graph memory | 0.95 | +0.10 | $0 | local | <1 | 0 | $0 |

Exact machine-dependent latency is retained in `runs/summary.json`; all p95
values were below one millisecond. Compound progression:
`0.50 → 0.65 → 0.85 → 0.95`. Every lift exceeds the 0.02 noise floor.

The reflection stage fixes absent remediation when the cause is explicit. The
tool stage fixes guessed/missing ownership using `owners.json` and confirms type
and non-emptiness on every result. The graph stage fixes recurrence detection.

## Decision point and skipped stages

Rules 1–3 favor the least expensive reliable pattern. Planning was skipped
because one report maps to one bounded analysis with no dependent tool sequence;
the total path is three deterministic operations. Multi-agent review was skipped
because the five fields do not expose distinct security/correctness/robustness
stances: adding reviewers would reproduce the Module 6 echo-chamber risk without
a measured error class. Routing was also unnecessary because all inputs share
the same contract and risk family.

These are not omissions disguised as future work. The task's measured failures
were missing remediation, ownership, and recurrence. Reflection, one real-data
tool, and graph memory directly address those failures.

## Graph evidence and Rule 5

The capstone task adapter uses the existing executable five-node/five-edge
`GraphStore`, canonical entity ids, source hashes, verbatim spans, additive
claims, and run records. Twenty reads and twenty writes give a 1.0 read/write
ratio. The historian is the direct reader and the extractor the writer; 50% of
reads cross sessions. The graph therefore passes Rule 5 on the cross-session
criterion even though it does not need multiple reading roles.

| Subset | Without graph (tools) | With graph | Δ |
|---|---:|---:|---:|
| First encounter | 1.00 | 1.00 | 0.00 |
| Repeat pattern | 0.70 | 0.90 | +0.20 |
| All | 0.85 | 0.95 | +0.10 |

This is the expected persistent-world-model shape: no benefit when the system
knows nothing yet, material benefit on repeat patterns, and diluted aggregate
lift. Five hard remediations remain wrong, preventing a sanitized perfect score.

## Production readiness

Every claim write has a hashed incident-report source and a verbatim span.
Arguments and outputs use strict Pydantic schemas. The owner tool is read-only,
raises on an unknown service, and requires confirmation. Execution is bounded to
one pass through the fixed chain. The unified course logs and generated dashboard
live at repository level under `runs/` and `reports/`.

The main production limitation is corpus realism: these are controlled incident
reports, not a representative operational sample. Before deployment, collect
de-identified real reports, add ambiguity and multiple-cause cases, and require
human approval for severity or ownership changes.
