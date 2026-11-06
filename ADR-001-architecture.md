# ADR-001: Ship a Gated Direct Reviewer with a State File, Not a Graph

- **Status:** Accepted
- **Date:** 2026-11-05
- **Decision owner:** Repository maintainer
- **Measurement source:** Frozen Modules 1–6 artifacts
- **Noise floor:** **0.0667 F1**; a delta must be greater than this to demonstrate lift

## 1. Context

The system reviews self-contained Python snippets and returns a structured list of defects with exact
category, line, severity, and rationale. Dataset 1.1.0 contains 20 frozen measurement items (six easy,
ten medium, four hard) with seeded category-and-line labels. The scorer computes deterministic exact
match precision, recall, and F1; no model judge is involved. Two unchanged zero-shot runs scored 0.8786
and 0.9452, establishing the 0.0667 noise floor used throughout this audit.

Modules 1–6 tested reflection, tools, planning, role separation, panels, gates, routing, voting, and
orchestration. This ADR consolidates their existing artifacts without new model calls. Results from
different scopes are retained but not treated as directly comparable: Module 5 and the orchestrator use
three items, Module 6 gate experiments replay 20 items with deterministic fault fixtures, and the core
baseline through planning uses 20 live items.

## 2. Measured progression

| Stage | Mean score | Δ vs previous | Tokens/item | Cost/item | p50 latency | p95 latency | Cost/score point |
|---|---:|---:|---:|---:|---:|---:|---:|
| Zero-shot baseline | 0.8786 | — | 1,049 | $0.00720 | 2.64s | 3.46s | $0.00820 |
| Reflection (M2) | 0.9452 | +0.0667† | 3,018 | $0.01759 | n/a | n/a | $0.01861 |
| Tool use (M3) | 0.8833 | −0.0619† | 5,800 | $0.03345 | 5.02s | 7.16s | $0.03787 |
| Planning (M4) | 0.8436 | −0.0398† | 7,568 | $0.06366 | 22.58s | 40.10s | $0.07546 |
| Generator–critic (M5, 3 items) | 1.0000 | +0.1564‡ | 5,625 | $0.05352 | n/a | n/a | $0.05352 |
| Review panel (M5, 3 items) | 1.0000 | 0.0000† | 2,652 | $0.03443 | 7.24s | 7.55s | $0.03443 |
| Gated chain (M6 replay) | 0.8786 | −0.1214† | 0 incremental | $0 | 0 incremental | 0 incremental | $0 |
| Routed (M6 frozen routes) | 0.8686 | −0.0100† | 4,815 | $0.03874 | 15.14s | 35.32s | $0.04461 |
| Orchestrator (M6, 3 items) | 1.0000 | +0.1314‡ | 2,652 | $0.03443 | 7.24s | 7.55s | $0.03443 |

† Delta did not exceed the 0.0667 noise floor. ‡ Delta exceeded it numerically but compares different
sample scopes and is not promotable evidence. Historical percentile latency was not retained for M2 or
M5 generator–critic; this audit does not buy replacement runs to manufacture it.

Raw full-set progression: **0.8786 → 0.9452 → 0.8833 → 0.8436 → 0.8786 → 0.8686**.
Promotion-adjusted progression, flattening changes that did not clear noise: **0.8786 → 0.8786 →
0.8786 → 0.8786 → 0.8786 → 0.8786**. The experiments improved observability and controls, not
demonstrated full-set model quality. Gates matter because they exposed a 15% seeded silent-late failure
rate, while extra agents and planning primarily increased tokens and latency.

## 3. Current architecture

Ship the frozen single-call reviewer behind deterministic input/output gates, with human review for
high-impact findings and a JSONL state/audit file recording prompt version, output, gate verdicts,
approval, and provenance. Do not ship reflection by default, the planner, router, permanent review
panel, or transcript orchestrator. Specialists may be invoked only through an evidence-backed route.

The measured model path costs **$0.00720/item**, uses **1,049 tokens/item**, and has **3.46s p95**
latency. Deterministic gates add no model tokens and negligible local latency. At 100× the evaluation
volume (2,000 items), projected model cost is approximately **$14.41** before volume or pricing changes.

## 4. Decision-rule assessment

### Rule 1 — Start with the cheapest pattern

The project did start with zero-shot. Reflection targeted unstable line attribution and speculative
extras (items 012 and 006). Tools targeted five classified grounding/capability failures; planning
targeted the multi-defect coherence failure on item 017; specialist critics targeted precision and
shared-state blind spots on items 011 and 018. Gates targeted the measured class “well-formed but
semantically invalid,” later reproduced at 3/20. The router and large orchestrator were curriculum
stress experiments rather than responses to a production failure and are flagged as unmotivated for
the shipped system.

### Rule 2 — Measure before promoting

| Stage | Pre-stage failure rate | Threshold/consequence adjustment | Verdict |
|---|---:|---|---|
| Reflection | 2/20 named line/speculation failures (10%) | Above 5%, but lift only equals noise | Marginal |
| Tools | 5/20 targeted failures (25%) | Fixed only one named case; +0.0048 vs baseline | Not justified |
| Planning | 1/20 multi-defect coherence case (5%) | At threshold; quality regressed | Not justified |
| Generator–critic | 2/20 precision/assumption concerns (10%) | Three-item evidence; +0.0548 vs reflection below noise | Marginal |
| Review panel | 2/20 specialist blind spots (10%) | Zero unique findings and zero score delta on tested subset | Not justified |
| Gated chain | 3/20 seeded silent-late failures (15%) | All rescued; deterministic control is cheap | Justified |
| Router | 4/20 hard items (20%) | 15 over-routes, one under-route; worse score and cost | Not justified |
| Orchestrator | 0% in proposed ship path | Bottleneck begins only at forced team size 10 | Not justified now |

Sensitivity: stages well below noise would need more than 0.0667 full-set lift to flip. Reflection is
the marginal case: any reproducible improvement above its current +0.0667 would justify promotion.

### Rule 3 — Match control to risk

The reviewer is **medium risk overall and high risk for security/data-integrity findings**: it advises
humans but performs no external mutation. Predictable code gates, constrained output, explicit failure,
and human approval match that risk. A bare autonomous call or free-form planning agent would not.

### Rule 4 — Count tokens, not agents

The best comparable shippable path uses 1,049 tokens/item. On the three-item Module 5 budget test, every
architecture scored 1.0: one-pass critic used 1,580 tokens/item, best-of-three 1,831, panel 2,652, and
three passes 5,625. More tokens did not improve score. Module 6 likewise showed transcript context grew
11.96× faster per worker than typed artifacts. The direct gated call is the best tested use of budget.

### Rule 5 — The graph earns itself

Three legitimate prospective queries exist:

1. **Critic/evaluator/release monitor:** “Which outputs for this item and prompt version changed category
   or line across prior runs?” Crosses sessions.
2. **Reviewer UI/auditor:** “Which source span, worker finding, gate verdict, and approval supports this
   final defect?” Primarily within a session, retained across sessions for audit.
3. **Generator/critic/evaluator:** “Which assumptions about this API or shared state were rejected before,
   by whom, and with what evidence?” Crosses sessions.

These queries have multiple readers, but current volume and relationships fit indexed JSONL records.
The queries justify structured state, not yet graph operational complexity.

## 5. Criteria assessment

| Criterion | Binds? | Evidence |
|---|---|---|
| Session persistence | No | Each review item is self-contained; runtime quality does not require facts from a prior session. |
| Cross-agent coordination | No, for the ship path | A transcript orchestrator lost the seed at 10 workers and had a 11.96× token slope, but the selected architecture has one reviewer and gates. |
| Traceability | Yes | Exact line/category scoring, gate rescues, and changed findings require durable provenance; Modules 1 and 6 expose these changes. |

Traceability is the only binding criterion. It drives the middle-path decision: persist an append-only
state file now. Cross-agent coordination would become binding if the system actually required large
teams; the stress experiment alone is not a reason to deploy them.

## 6. Anti-pattern audit

| Anti-pattern | Metric | Value | At risk? | Remediation |
|---|---|---:|---|---|
| Everything-agent | Responsibilities expressible in one sentence | 8/8 roles | No | Keep schemas and role boundaries narrow. |
| Echo chamber | M5 mean pairwise Jaccard | 1.00 | **Yes** | Drop the permanent panel; route specialists only on relevant risk. |
| Infinite loop | Forced M5 loops ending at cap; score slope after iteration 2 | 100% of 3; 0.000 | **Yes** | Stop on accept; permit at most one evidence-backed revision. |
| Phantom graph | Named graph queries with >1 reader | 3 | No | Start with indexed JSONL; graduate only on measured query pain. |
| Conversational bottleneck | Transcript/artifact slope; seed survival at 10 | 11.96×; 0% | **Yes** | Bounded artifacts, then hierarchy/shared store. |
| Missing baseline | Frozen runs and noise floor | 2 runs / 20 items; 0.0667 | No | Preserve dataset, prompt, scorer, and run metadata. |
| Premature agent | Best comparable full-set lift vs baseline | +0.0667 = noise | **Yes** | Do not promote agents until repeated lift exceeds 0.0667. |

## 7. Decision

**Proceed with a state file, not a graph.** Ship one constrained reviewer plus deterministic semantic
gates and human approval. The state file holds run/item ids, prompt and model versions, input hash,
structured output, assumptions, gate verdicts, provenance, score, human disposition, latency, token
usage, and cost. It supports the current traceability requirement without graph infrastructure.

Graduate to a graph only if at least one of these triggers is observed: runtime decisions depend on
facts from prior sessions; three or more active agents repeatedly query shared facts; JSONL joins for
the three named queries exceed operational latency/SLOs; or trace traversal becomes incomplete. At
that point the graph should target measurable provenance-query latency and zero omission—not an
unspecified “smarter architecture.”

## 8. Consequences

This decision commits the project to a cheap, predictable, auditable path and to append-only state with
versioned schemas. It forecloses autonomous planning, default multi-agent review, and graph operations
until evidence changes. Some hard items will still be missed; human review remains necessary for
security and data-integrity findings.

The regression dashboard will monitor: (1) exact-match F1 and delta versus the 0.0667 noise floor,
(2) gate-fire, rescue, and confident-wrong rates, and (3) cost/tokens plus p95 latency per item. The ADR
is wrong if repeated full-set runs show another configuration clearing the noise floor, if cross-session
facts become required, or if state-file provenance queries become slow or incomplete.

## Reproducibility

Consolidated machine-readable values are in `runs/architecture-audit.json`; generation is offline via
`PYTHONPATH=. python3 evals/summarize_architecture.py`. New API spend for this audit: **$0.00**.

