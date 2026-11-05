# Lab 4.1 report — validated planning

## Candidate subset frozen before measurement

Planning candidates were fixed in `evals/planning_candidates.json` before any planning run: items 006, 011, 012, 017, and 018 (5/20, exactly one quarter). They represented unstable precision, line attribution, multi-defect coherence, or missed concurrency concerns. The other 15 short, mostly single-defect snippets already scored well and were expected to need only a cheaper path.

## Quality and verdict

| Pipeline | Full-set mean F1 | Delta vs baseline run 1 | Cost |
|---|---:|---:|---:|
| Baseline | 0.8786 | — | $0.144060 |
| Reflection | 0.9452 | +0.0667 | $0.351780 |
| Tools | 0.8833 | +0.0048 | $0.669085 |
| Planning | **0.8436** | **-0.0350** | **$1.273165** |

Planning scored **0.5476 on the five candidates**. It therefore improved neither the full set nor the subset beyond the 0.0667 noise floor; it regressed both. The cost multiple was **8.84×** the direct baseline, close to the course's ~10× warning. There is no positive cost-per-point because quality did not improve. Reflection remained the best measured investment.

The honest verdict is **do not ship universal planning for this task**. Even a router to the nominated subset is not justified by these results: planning particularly underperformed on the cases selected for decomposition. A future router should instead target a revised, specialist tool surface and be re-evaluated before deployment.

## Plan and execution health

First-attempt plan validity was **95%**. The only violation was one seven-step plan exceeding the six-step bound; revision corrected it. No item was abandoned. Plans executed a mean **4.6 steps** (distribution: five 3-step, five 4-step, four 5-step, five 6-step, one 7-total-step item across replans). Step success was **96.74%**. Three tool calls returned payloads but failed their declared success criteria, preventing empty static-smoke results from cascading as evidence. Replan rate was 15%; escalation rate was 0%; no item exceeded the ten-total-step bound.

The schema and validator live in `agents/plan_validator.py`; all seven checks return named, step-specific violations. `agents/planner.py` preserves bounded artifacts, computes DAG order, limits plans/replans/total steps, counts strikes by logical tool step, and emits structured `completed`, `failed`, and `blocked_by` fields on escalation. `runs/planning/item-006/trace.jsonl` shows initial plan, artifacts, criterion failure, a replan receiving prior results, and synthesis.

## Cost engineering and caching

The full run used 125,553 input, 25,816 output, and **48,024 cache-read tokens**. Mean latency was 24.41 seconds/item; p95 was 40.07 seconds. Stable planner instructions and tool definitions were cached; every step artifact was typed and capped rather than appending raw transcripts; plan and total-step bounds limited context growth.

On the same five candidates, the cached run cost **$0.330130** versus **$0.505740** without caching: a measured saving of **$0.175610 (34.72%)**. Cache reads were 12,006 tokens versus zero. Scores differed (0.5476 cached, 0.6810 uncached) because model planning is nondeterministic, so this is a cost observation rather than a causal quality claim.

Task-budget tokens were passed to every plan and synthesis call, with `max_tokens` as the hard backstop. The negative quality result was not caused by unbounded spending: it occurred despite the required cost controls.
