# Module 9 — Multi-Agent Systems on Graphs

## Method and cost boundary

This lab is a deterministic replay over the committed Module 2 outputs and the
Module 8 knowledge graph. It made **no new model calls and spent $0 in new API
cost**. That makes the comparison reproducible and inexpensive, but it does not
pretend that local graph-query latency is equivalent to live model latency.

## Lab 9.1 — Graph-grounded evaluator

The composite order is: deterministic gates, graph verification, then rubric
evaluation only for survivors. The parser canonicalizes file and defect-category
entities, normalizes predicates to the vocabulary already present in the graph,
and logs unmappable predicates. Unparseable claims remain a separate verdict.

| Metric | Rubric only | Graph only | Composite |
|---|---:|---:|---:|
| Mean score | 0.8786 | 0.8786 | 0.9452 |
| Delta vs Module 2 baseline | — | 0.0000 | +0.0667 (equal to noise floor) |
| Structured-claim coverage | — | 100% | 100% |
| Findings per item | 1.30 | 1.30 | 1.30 |
| Findings with source spans | 0 | 17 | 17 |
| Supported / unsupported / contradicted | — | 15 / 9 / 2 | 15 / 9 / 2 |
| Finding precision, hand-checked sample (n=20) | 80.8% | 100% | 100% |
| Mean iterations | 1.0 | 1.0 | 1.0 |
| Tokens / cost per item | 1048.6 / $0.00720 | 0 / $0 | 3018 / $0.01759 |

Coverage is 100% only for the structured `defects[]` factual claims this parser
declares in scope. It is **not** 100% coverage of arbitrary prose or implicit
reasoning. This is the approach's hard ceiling: free-form assertions outside the
contract require another parser and must be reported as unparseable.

The two observed contradictions were hand-checked as graph-right/draft-wrong
extra categories. A controlled low-confidence disagreement exercised the harder
case: the draft was right and the graph was wrong. Provenance weighting changed
the action from `remove` to `investigate`; a new provenance-backed claim and
`contradicts` edge were prescribed. Result: one graph-improvement write and one
wrong correction prevented. The controlled case is identified separately so it
is not misrepresented as a naturally observed corpus event.

### Three under-one-minute verification examples

1. `range_total.py` / `(file, has_defect, off_by_one)`: the deciding current
   claim and source `range_total.py` cite `for i in range(n + 1):`; action `cite`.
2. `tags.py` / `(file, has_defect, mutable_default)`: the deciding claim cites
   `def add_tag(tag, tags=[]):`; action `cite`.
3. `config.py` / `(file, has_defect, swallowed_exception)`: the deciding claim
   cites `except Exception:`; action `cite`.

The exact claim ids, locators, verbatim spans, confidence, and graph statements
are preserved in `runs/graph-evaluator-summary.json`, so each check needs no code
access and can be completed in under a minute.

## Lab 9.2 — Graph-orchestrated system

The role registry is executable data. Architect, tech lead, developer, and
historian have callable read queries and code-enforced write scopes. A forbidden
write test exists for every role. Workers independently open and query the graph;
the handoff returns only control metadata and graph ids. Independent reads run
concurrently, and synthesis performs a bounded graph query rather than receiving
worker transcripts.

| Information | Graph or handoff | Why |
|---|---|---|
| Plan step assignments | Handoff | Run-local control flow |
| Completion criterion | Handoff | Describes what happens next |
| Completion status and written ids | Handoff | Boundary/control acknowledgment |
| Extracted entity claims | Graph | Expected to remain true tomorrow |
| Review findings | Graph | Supports later pattern detection |
| Provenance and source span | Graph | Durable audit evidence |
| Role prompt and effort | Run node | Reproducibility metadata |

Concurrent entity writes use canonical, idempotent upserts. Workers append claim
candidates. The tech lead serializes supersedes after checking the current claim
id; workers never race to replace history silently.

### Context scaling and finding survival

| Team | Transcript tokens | Artifact tokens | Graph tokens |
|---:|---:|---:|---:|
| 3 | 2,308 | 202 | 86 |
| 5 | 3,841 | 328 | 87 |
| 10 | 7,672 | 646 | 88 |
| 20 | 15,337 | 1,291 | 89 |

Slopes are 766.40, 64.10, and **0.16 tokens per added worker** respectively.
Across three deterministic runs per cell, transcript finding survival was
100%, 100%, 0%, 0%; artifact and graph survival were 100% at every team size.

### Rule 5 audit (three sessions)

| Type | Writes | Reads | R/W | Reader roles | Cross-session rate | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Entity | 30 | 96 | 3.20 | 4 | 67% | Keep |
| Claim (finding) | 24 | 81 | 3.38 | 3 | 62% | Keep |
| Claim (extracted) | 63 | 132 | 2.10 | 4 | 58% | Keep |
| Source | 15 | 48 | 3.20 | 3 | 54% | Keep |
| Artifact | 15 | 1 | 0.07 | 1 | 0% | **Remove from graph** |
| Run | 3 | 14 | 4.67 | 2 | 71% | Keep for audit |

`Artifact` fails Rule 5. Production should keep artifact content references in a
normal PostgreSQL relational table/object store rather than paying graph overhead.
This is consistent with ADR-002: PostgreSQL is the production system of record;
SQLite remains the local/test backend.

### Persistent-world-model effect

| Subset | Without graph | With graph | Delta |
|---|---:|---:|---:|
| First encounter | 0.8786 | 0.8786 | 0.0000 |
| Repeat pattern | 0.8786 | 1.0000 | +0.1214 |
| All items | 0.8786 | 0.9393 | +0.0607 |

The repeat-pattern lift exceeds the 0.0667 noise floor; the aggregate lift does
not. The benefit is correctly concentrated where durable knowledge exists.

## Full-stack progression

The authoritative stage metadata and scope caveats are in the generated JSON.
Some later stages used smaller deterministic subsets, so this is an architectural
progression, not a statistically clean head-to-head leaderboard.

| Stage | Mean score | Cost/item | p95 latency |
|---|---:|---:|---:|
| Zero-shot baseline | 0.8786 | $0.00720 | 3.46 s |
| + reflection | 0.9452 | $0.01759 | not retained |
| + tool use | 0.8833 | $0.03345 | not retained |
| + planning | 0.8436 | $0.06366 | 40.10 s |
| + multi-agent | 1.0000 | see JSON | subset only |
| + graph | 0.9393 | $0 new | 0.01 s local replay |

Compound line: `0.8786 → 0.9452* → 0.8833 → 0.8436 → 1.0000
(subset) → 0.9393 (two-pass replay)*`, where `*` marks a delta at or within the
measured noise floor or a non-comparable scope.
