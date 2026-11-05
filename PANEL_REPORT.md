# Module 5.2 — Three-Rubric Panel Report

## Distinctness before measurement

The panel uses the Parallelization pattern: correctness, security, and robustness reviewers receive
the same immutable task and generator artifact concurrently, then a deterministic code path merges
their findings. Thresholds were frozen before any calls: pairwise Jaccard above **0.60** indicates
redundancy; unique contribution below **0.10** means a role does not earn its cost.

| Rubric pair | Defect the first catches and the second does not | Defect the second catches and the first does not |
|---|---|---|
| Correctness / security | Off-by-one prefix summation | SQL injection from interpolated input |
| Correctness / robustness | Wrong cache key returns another currency | Missing timeout hangs on a peer |
| Security / robustness | Authorization OR condition permits bypass | File handle leaks on an exception |

The arguments are structurally distinct even though this three-item sample did not exercise the
differences. Prompts and rubrics are stable, narrow, and separately cacheable.

## Echo-chamber test

| Metric | Value | Threshold interpretation |
|---|---:|---|
| Mean Jaccard, correctness–security | 1.000 | redundant |
| Mean Jaccard, correctness–robustness | 1.000 | redundant |
| Mean Jaccard, security–robustness | 1.000 | redundant |
| Unique contribution, correctness | 0.000 | fails 0.10 minimum |
| Unique contribution, security | 0.000 | fails 0.10 minimum |
| Unique contribution, robustness | 0.000 | fails 0.10 minimum |
| Defects found by all three | 0 | none |

Jaccard is defined as 1.0 when both sets are empty: the roles behaved identically by returning no
findings. Thus the result is not “all three discovered the same hard defect”; it is “none added a
finding after the generator produced correct artifacts.” The perfect score and empty sets create a
ceiling effect, but the production decision is still clear: do not pay for this panel on equivalent
easy items.

## Formal role test

| Role | Unique defects | Score with | Score without | Delta | Added role + ablation cost | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Correctness | 0 | 1.000 | 1.000 | 0.000 | $0.03908 | Drop |
| Security | 0 | 1.000 | 1.000 | 0.000 | $0.04345 | Drop |
| Robustness | 0 | 1.000 | 1.000 | 0.000 | $0.04212 | Drop |

Every role fails the stated test on this sample. The defensible architecture is one combined critic by
default, with specialist routing only when task features indicate hostile input, concurrency, resource
handling, or another relevant risk class. “Drop” is the measured outcome, not a failed experiment.

## Tokens, not agents

| Configuration | Raw tokens/item | Cached tokens/item | Mean score | Measured cost |
|---|---:|---:|---:|---:|
| 1 combined critic, 1 pass | 1,580 | 4,962 | 1.000 | $0.05826 |
| 1 combined critic, 3 sequential passes | 5,625 | 14,886 | 1.000 | $0.16056 |
| 3 distinct critics, parallel | 2,652 | 10,138 | 1.000 | $0.10328 |
| Best-of-3 generation, 1 selector critic | 1,831 | 8,501 | 1.000 | $0.07241 |

The budgets are not exactly matched because schemas and output lengths differ, so observed token
counts are reported explicitly. All configurations tied on score. The one-pass combined critic was
therefore the best use of tokens. Best-of-3 was second-cheapest but added no quality; three sequential
passes were the least efficient. The panel’s separate role-ablation revisions cost another $0.05347
and are excluded from its primary-path token row.

## Latency and conclusion

Mean parallel reviewer latency was **6.62s** versus an estimated **17.33s** if the three independent
reviewers ran sequentially: a **10.71s (61.8%) reduction**. Parallelization works operationally, but
speed does not justify reviewers that add no defects or score lift.

The recommended system has one generator plus one combined, adversarial critic, with deterministic
gates and conditional specialist routing. Re-run this test on more adversarial cases before deciding
that specialists are universally unnecessary.

## Reproducibility

- Panel metrics and ablations: `runs/panel/summary.json`
- Token comparison: `runs/module5-token-budget.json`
- Declared thresholds and distinctness examples: `evals/panel_distinctness.json`
- Per-item merged artifacts: `runs/panel/item-001/result.json`

