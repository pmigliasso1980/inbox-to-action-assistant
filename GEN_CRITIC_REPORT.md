# Module 5.1 — Generator–Critic Report

## Method

The generator and critic use the same model but different stable system prompts. The generator owns a
bounded `GeneratorArtifact`; the critic takes an explicitly adversarial external-reviewer stance and
returns a bounded `CriticArtifact`. Each handoff is schema-validated, checks ids and line references,
enforces size bounds and the blocking-defect decision invariant, and permits one correction before
escalation. The critic receives only the immutable task, rubric, and declared artifact—not generator
conversation history. Every artifact points to a JSONL transcript through `trace_id`.

To control API cost, measurement used the first three frozen evaluation items. The adversarial and
neutral configurations were forced through three passes so their architecture and opportunity to
revise were identical. This sample is suitable for a lab demonstration but too small for a production
decision; score saturation is reported rather than hidden.

## Results against Module 2

| Metric | Module 2 reflection (20 items) | Module 5 generator–critic (3 items) |
|---|---:|---:|
| Mean score | 0.9452 | 1.0000 |
| Delta vs baseline | +0.0667 | +0.1214 |
| Accept/satisfied at iteration 1 | 100% | 100% |
| Mean iterations | 1.00 | 3.00 (forced for ablation) |
| Blocking defects/item | not recorded | 0.00 |
| Assumptions declared/item | not recorded | 4.00 across passes |
| Assumptions rejected | not recorded | 1 |
| Gate failure rate | 0% | 0% |
| Raw input + output tokens/item | 3,018 | 5,625 |
| Cached read tokens/item | 1,621 | 14,886 |
| Cost/item | $0.01759 | $0.05352 |

The score increase over reflection is **0.0548**, below the pre-measured **0.0667 noise floor**. The
role split therefore did not demonstrate a reliable quality improvement on this ceiling-saturated
subset. Accept-at-one did not drop, and later passes did not improve the already-perfect score. The
extra passes mostly bought audit evidence and assumption scrutiny, not measured F1.

The best finding was on item 003. The generator assumed callers could not distinguish the fabricated
`"{}"` fallback from a legitimate empty configuration. The adversarial critic rejected that caller
claim because no caller appeared in the snippet, while preserving the independently supported
`swallowed_exception` defect. This is precisely the value of a declared assumption: unsupported
reasoning became visible without invalidating a sound finding.

At roughly 3.04× the per-item cost of Module 2, three forced passes were not worth deploying for this
task. A single gated pass is the cost-efficient default; escalation should be conditional on a critic
finding or low confidence.

## Stance ablation

| Metric | Adversarial critic | Neutral critic | Change |
|---|---:|---:|---:|
| Accept at iteration 1 | 100% | 100% | 0 pp |
| Blocking defects/item | 0.00 | 0.00 | 0.00 |
| Mean score | 1.0000 | 1.0000 | 0.0000 |
| Assumptions rejected | 1 | 0 | -1 |
| Cost | $0.16056 | $0.16380 | +$0.00324 |

The stance did not move score or acceptance because all three outputs were already correct, but it did
change critic behavior: only the adversarial critic challenged an unsupported assumption. This is a
small-sample signal, not proof. A broader, harder dataset would be required before assigning the
adversarial configuration permanently.

## Reproducibility

- Primary metrics: `runs/gen-critic/summary.json`
- Neutral ablation: `runs/gen-critic-neutral/summary.json`
- Readable artifacts and gates: `runs/gen-critic/item-003/iter-1.json`
- Full transcript: `runs/gen-critic/item-003/transcript.jsonl`

