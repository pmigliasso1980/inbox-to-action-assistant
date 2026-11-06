# Module 6.1 — Gated Chain and Calibrated Router

## Cost-control method

No new model calls were made. The experiment replays the immutable outputs already purchased for the
Module 1 baseline, Module 2 reflection loop, and Module 4 planner. Deterministic fault fixtures make
gate behavior repeatable, while route quality is computed from the real frozen per-item scores, costs,
and latencies. This saves money and avoids changing model behavior between control and treatment. It
also means router confidence comes from a deterministic classifier rather than a newly paid cheap-model
call; production deployment should validate that replacement with fresh traffic.

## Chain stages and contracts

| Stage | Input → output | Model / effort | Tools | Constrained | Justification |
|---|---|---|---|---|---|
| `normalize` | task → `SourceArtifact` | code / none | no | Pydantic | Parsing, identity, and line preservation are deterministic. |
| `identify_candidates` | source → `CandidateArtifact` | frozen baseline replay / low | no | Pydantic | Reuses paid extraction output; a live version maps to the cheapest review call. |
| `rank` | candidates → `RankedArtifact` | code / none | no | Pydantic | Severity ordering and bounds need no judgment call. |

`source_to_candidates` checks schema, non-empty lines, file identity, and semantic line-count
preservation. Its fallback is **retry with a specific complaint**. `candidates_to_rank` checks taxonomy,
line references, bounds, plus semantic evidence such as a division operator for `division_by_zero` or
SQL text for `sql_injection`; its fallback is **escalate to the capable expert path**. `rank_to_output`
checks duplicate findings, line references, and the cross-field rule that confident output cannot be
empty; its fallback is **explicit failure**. Thus each boundary has a semantic check and the workflow
uses three fallback strategies, two of which are required by the lab.

The chain keeps model use to one replayed stage, so it does not fragment a cache across models.
Historical evidence reinforces the choice: baseline and reflection recorded zero cache-read tokens,
while the stable-prefix planning workflow recorded 48,024. Cacheability depends on stable prefixes and
repeated traffic, not merely splitting a task into more calls.

## Ungated versus gated

| Metric | Ungated | Gated |
|---|---:|---:|
| Mean score | 0.7286 | 0.8786 |
| Items where a gate fired | 3 | 3 |
| Gate-signaled items still producing confident wrong output | 3 | 0 |
| Items rescued by fallback | 0 | 3 |
| Items explicitly failed | 0 | 0 |
| New API cost | $0 | $0 |
| Added model latency | 0 | 0 |

The prominent result is a **15% silent-late failure rate (3/20)** in the ungated fixture. These were
well-formed, high-confidence outputs that ordinary schema validation would allow. All three were
rescued when gates controlled flow.

Worked example: item 004 contains a SQL query built with an interpolated `name` on line 2. The seeded
candidate stage emitted a plausible `sql_injection` finding but cited line 99 and stated confidence
0.94. Ungated flow ranked and returned it, producing score 0 despite looking valid. The reference gate
reported `candidate 0 line 99 does not exist`; the gated path escalated and returned the verified line
2 finding, producing score 1. The complete trace is `runs/chain/gated/item-004.json`.

## Router calibration

Routes are `simple` (baseline), `standard` (reflection/gated review), `complex` (planner), and mandatory
`other` (most capable path / human queue). Global threshold is 0.80. Because under-routing security and
multi-defect cases can miss high-impact findings, standard requires 0.85 and complex 0.90.

| Confidence bucket | N (first 10) | Actual routing accuracy |
|---|---:|---:|
| 0.5–0.7 | 0 | n/a |
| 0.7–0.8 | 0 | n/a |
| 0.8–0.9 | 6 | 0% |
| 0.9–1.0 | 4 | 75% |

Accuracy rises with confidence, but the empty low buckets and only ten calibration items make this
weak evidence. Threshold 0.80 is not acceptable: the 0.8–0.9 bucket was entirely wrong. A provisional
0.90 automatic-routing threshold is safer; lower confidence should take `other` until more cases are
collected. Across all 20 items there were 15 over-routes and one under-route. Under-routing is worse for
this review task because it can miss a defect, but over-routing dominated cost without buying quality.

## Router value

| Configuration | Mean score | Historical cost | Mean latency |
|---|---:|---:|---:|
| Everything through cheapest | 0.8786 | $0.1441 | 2.78s |
| Everything through most expensive | 0.8436 | $1.2732 | 24.41s |
| Routed | 0.8686 | $0.7749 | 13.64s |

The router is **not a win**. The cheapest route scored better than both alternatives, and planning was
more expensive but worse on this narrow defect-identification task. The problem is not merely threshold
choice: these destinations are insufficiently differentiated. Production should keep the simple path,
use deterministic gates, and route only on a demonstrated specialist need. The failed value hypothesis
is the useful result.

Artifacts: `agents/workflow_patterns.py`, `runs/chain/summary.json`, `runs/router/summary.json`.

