# Module 6.2 — Parallelization and the Orchestrator Bottleneck

## Measurement method

Sectioning reuses actual Module 5 panel timings and token counts. Voting uses deterministic voters over
the ten medium/hard frozen items so stance and evidence diversity are controlled exactly. Orchestrator
scaling uses bounded typed artifacts and deliberately verbose transcripts under a fixed 5,000-token
synthesis budget. Each silent-omission cell is repeated three times. These are reproducible context
experiments, not claims about stochastic model behavior; new API cost is $0.

## Sectioning

| Metric | Sequential | Sectioned in parallel |
|---|---:|---:|
| Mean wall-clock latency | 17.33s | 6.62s |
| Observed max latency (three-item p95 proxy) | 19.37s | 7.58s |
| Total tokens | 7,955 | 7,955 |
| Mean score | 1.000 | 1.000 |

Parallel sectioning reduced mean latency by 61.8% while tokens and score stayed fixed. The sections did
not duplicate context in this replay. With only three observations, the reported upper-tail number is
an observed maximum rather than a statistically stable p95.

## Voting diversity

| Metric | Repeat | Distinct rubrics | Distinct evidence |
|---|---:|---:|---:|
| Mean aggregated score | 0.7905 | 1.0000 | 1.0000 |
| Mean pairwise agreement | 1.0000 | 0.2667 | 0.2333 |
| Mean unique contribution, voters 1/2/3 | 0/0/0 | .45/.23/.32 | .83/.13/.03 |
| Tokens | 31,959 | 31,959 | 31,959 |
| Score improvement over N=1 | 0.0000 | 0.5333 | 0.1167 |

Repeated identical work produced perfect agreement and no gain: repetition was not diversity.
Rubric and evidence variants reduced agreement and added complementary findings. Evidence voter 3 fell
below the earlier 0.10 contribution threshold, showing that equal worker count is not automatically a
good partition.

| Rubric aggregation | Mean score | Precision | Recall |
|---|---:|---:|---:|
| Majority | 0.0000 | 0.0000 | 0.0000 |
| Union + dedupe | 1.0000 | 1.0000 | 1.0000 |
| Intersection | 0.0000 | 0.0000 | 0.0000 |
| Best by deterministic score | 0.9467 | 1.0000 | 0.9167 |

Best-by-score beat majority as predicted, but did **not** beat union. The three rubrics own disjoint
error classes, so majority and intersection erase correct minority evidence. A high-precision union is
the appropriate aggregator here. The scorer is deterministic exact-match F1, not a model judge, so no
judge-agreement caveat applies.

## Orchestrator scaling and silent omission

The orchestrator dynamically selects correctness, security, robustness, and interaction workers from
each item’s risk profile; fixed team sizes below are explicit stress overrides.

| Team | Mode | Input tokens | Score | Context errors | Compacted |
|---:|---|---:|---:|---:|---|
| 3 | artifact | 202 | 1.0 | 0 | no |
| 3 | transcript | 2,308 | 1.0 | 0 | no |
| 5 | artifact | 328 | 1.0 | 0 | no |
| 5 | transcript | 3,841 | 1.0 | 0 | no |
| 10 | artifact | 646 | 1.0 | 0 | no |
| 10 | transcript | 7,672 | 0.9 | 0 | yes |
| 20 | artifact | 1,291 | 1.0 | 0 | no |
| 20 | transcript | 15,337 | 0.9 | 0 | yes |

Transcript input grew at **11.96×** the per-worker slope of bounded artifacts.

| Team | Artifact survival (3 runs) | Transcript survival (3 runs) |
|---:|---:|---:|
| 3 | 100% | 100% |
| 5 | 100% | 100% |
| 10 | 100% | 0% |
| 20 | 100% | 0% |

The distinctive `SENTINEL-ZEBRA-7319` finding began disappearing in transcript mode at team size 10.
There was no exception, warning, or context error: synthesis silently omitted it. Bounded artifact mode
preserved it at every size.

At team size 20, hierarchical synthesis reduced final input to 217 tokens and preserved the seed. The
file-backed shared store reduced queried input to 76 tokens and also preserved it. The store stops
orchestrator context from growing with team size because the orchestrator retrieves matching findings
instead of receiving every conversation.

## Transition argument

On this system, a flat transcript orchestrator stops being sufficient at **10 workers**: its 7,672
input tokens exceed the chosen synthesis budget, the seeded fact disappears in all three repetitions,
and no error reveals the loss. A flat orchestrator remains adequate for bounded typed artifacts through
20 workers, but state and retrieval concerns are already clearer as a graph/shared-store problem. Use
hierarchical synthesis as an interim fix; move to explicit persisted state when team size or audit needs
make selective retrieval necessary.

Artifacts: `agents/orchestrator_patterns.py`, `runs/orchestrator/summary.json`, and per-worker files
under `runs/orchestrator/team-*`.
