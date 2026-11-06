# Module 8.2 — Extraction and Data-Quality Audit

## Ground truth and extraction method

`evals/graph_ground_truth.jsonl` was fixed before extractor evaluation. It contains ten Python
documents with 20 entity mentions and ten claims; each document averages 2.0 labelled entities and 1.0
claim. On reread, no label changed: the exact line containing the seeded defect remained the support
criterion. This small agreement result is not an independent-annotator study.

To avoid token spend, `agents/extractor.py` is a schema-constrained deterministic extractor rather than
an LLM. It emits typed entities and subject/predicate/object claims with exact spans and confidence.
The rule set deliberately omits `resource_leak` and emits one plausible unsupported path-traversal
claim, preventing a meaningless perfect audit. New API cost is **$0.00**.

The write pipeline applies four gates: verbatim span verification with JSONL quarantine; schema
validation; canonical entity resolution plus near-match review flags; and same-subject/predicate,
different-object contradiction detection. It writes a fully configured Run node before any Claim.

## Extraction quality

| Entity metric | Value |
|---|---:|
| Precision | 0.9048 |
| Recall | 0.9500 |
| Missed | `resource_leak` category in `export.py` |
| Spurious | `path_traversal` in `config.py`; near-name `configs.py` |

| Claim metric | Value |
|---|---:|
| Precision | 0.9000 |
| Recall | 0.9000 |
| Missed | `export.py has resource_leak`, supported by `handle = open(...)` |
| Spurious | `config.py has path_traversal` |
| Claims failing verbatim span gate | 0 |
| Span passed but did not support statement | **1 of 10 checked** |

The unsupported `config.py` claim cites the verbatim function signature. Gate 1 correctly confirms the
text exists but cannot determine entailment. This is the lab’s central warning: provenance presence is
not provenance correctness.

## Entity resolution and contradictions

| Resolution metric | Value |
|---|---:|
| Incorrect merges | 0 |
| Incorrect splits | 0 |
| Near-match pairs flagged | 1 |
| Flags that were genuine duplicates | 0 |

The flagged `config.py` / `configs.py` pair scored 0.947 similarity and was correctly left separate for
review. The two competing `config.py has_defect` objects—`swallowed_exception` and
`path_traversal`—were both retained with one `contradicts` edge.

## Confidence calibration

| Confidence bucket | N | Actual correctness |
|---|---:|---:|
| 0.5–0.7 | 3 | 66.7% |
| 0.7–0.8 | 3 | 100% |
| 0.8–0.9 | 2 | 100% |
| 0.9–1.0 | 2 | 100% |

Correctness rises monotonically, but two examples cannot establish that the 0.9+ bucket is calibrated
to 90%; it happened to be 100%. The observed reliance threshold is **0.70** for low-risk retrieval.
For ADR’s highest-stakes security/data-integrity use, require **≥0.90 plus human inspection of the
span** until a much larger calibration set exists. Do not interpret the raw confidence as a probability.

## Whole-store audit

| Check | Result |
|---|---:|
| Schema conformance | 41 nodes checked; 0 errors |
| Claims with no provenance | **0** |
| Stale source hashes | **0** |
| High-similarity, different-id entity pairs | 1 |
| Confidence calibration | monotonic on 10 claims; small sample |
| Hand verification | 9/10 correct |

The quarantine file exists and is empty because every emitted span was verbatim. Tests separately prove
the stale-hash detector catches changed content.

## Amplification reflection

At 0.90 claim precision, roughly one in ten extracted claims is wrong yet durable and available to all
future agents. The graph is safe for discovery, candidate generation, audit navigation, and
human-reviewed assistance. It is not safe for autonomous security conclusions, approvals, or code
changes. The first fix is semantic entailment verification for each claim/span pair, followed by the
missing resource-management rule and a larger calibration set. I would require at least **0.98
precision with no high-severity unsupported claims** before the graph can drive ADR’s highest-stakes
query without mandatory human review.

Artifacts: `agents/extractor.py`, `graph/extraction_pipeline.py`, `graph/audit.py`,
`runs/graph-extraction-summary.json`, and `runs/graph-extraction-quarantine.jsonl`.

