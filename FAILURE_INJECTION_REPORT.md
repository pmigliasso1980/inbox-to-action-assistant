# Lab 2.2 failure-mode injection report

The same fixed subset, items 001–010 from dataset 1.1.0, was used for all five configurations. Predictions were frozen in `FAILURE_INJECTION_PREDICTIONS.md` before the runs.

| Run | Mean score | Δ vs control | Sat@1 | Mean iterations | Non-mono rate | Cost |
|---|---:|---:|---:|---:|---:|---:|
| control | 1.0000 | 0.0000 | 100% | 1.0 | 0% | $0.170020 |
| inject-self-confirm | 0.9667 | -0.0333 | 10% | 2.5 | 10% | $0.891190 |
| inject-drift | 0.9500 | -0.0500 | 100% | 1.0 | 0% | $0.140465 |
| inject-nonmono | 1.0000 | 0.0000 | 0% | 5.0 | 0% | $0.876150 |
| all-controls | 1.0000 | 0.0000 | 90% | 1.1 | 10% | $0.198560 |

## Self-confirmation was the most operationally expensive injection

Rubric drift lost the most score (-0.0500), while self-confirmation lost 0.0333 and cost more than five times control. That was not the prediction: self-confirmation reduced rather than increased Sat@1 because its vague, author-aligned task caused the critic to invent broad improvement requests. One critique demanded: “Re-scan the entire supplied snippet line by line and add every additional material defect you can support,” expanding scope rather than checking the immutable task.

## Rubric drift was hardest to detect from polished output alone

Drift retained 100% Sat@1 while score fell to 0.9500. On item 006 it approved three polished findings, including: “The HTTP POST has no timeout, so the call can hang indefinitely on an unresponsive server.” The sentence sounds professional, but the extra speculative findings reduced precision. This is the dangerous signature: fluent approval with a benchmark regression.

## Forced revision did not expose a score loss on this easy subset

The non-monotonic injection forced five iterations and returned the last draft, costing $0.876150, but every final score remained 1.0. No item had a non-final best draft, so the measured best-to-final gap was zero. The control remains necessary despite no observed benefit: this subset saturates the benchmark and therefore cannot reveal the failure reliably. The all-controls run matched control, not by more than the 0.0667 noise floor.

## Production monitoring metrics

1. **Self-confirmation — critic framing divergence:** alert when Sat@1 or mean iterations changes by more than 20 percentage points / 0.5 iterations from the validated control, or when critique vocabulary overlaps the generator restatement more than the immutable task.
2. **Rubric drift — factual-criterion coverage:** alert when more than 20% of critiques contain no issue tied to `concrete_defect`, `evidence_alignment`, `coverage`, or `precision`, especially when satisfaction remains high while benchmark score falls by more than the 0.0667 noise floor.
3. **Non-monotonicity — best-versus-final gap:** alert when more than 5% of items have a non-final best draft or mean best-minus-final score exceeds 0.02.

The interrupted first self-confirmation attempt is preserved in `runs/failed-partial-self-confirm/`; the successful rerun is the one used in the table.
