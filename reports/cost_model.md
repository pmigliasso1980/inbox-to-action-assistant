# Cost Model

Generated from `runs/calls.jsonl`.

## Per component

| Component | Calls | Mean input | Mean output | Mean cached | Cache % | Mean latency ms | Mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 40 | 950.6 | 98.5 | 0.0 | 0.0% | 3176.2 | $0.00722 |
| critic | 27 | 616.9 | 219.7 | 2234.2 | 78.4% | 1925.2 | $0.00858 |
| planner | 84 | 1494.4 | 306.9 | 571.6 | 27.7% | 5811.3 | $0.01516 |
| reflection | 40 | 1446.2 | 62.1 | 0.0 | 0.0% | 0.0 | $0.00879 |
| tools | 40 | 2788.9 | 111.3 | 0.0 | 0.0% | 2824.0 | $0.01673 |

## Per item

| Component | Mean cost | p95 cost | Mean latency ms | p95 latency ms |
|---|---:|---:|---:|---:|
| baseline | $0.00722 | $0.01105 | 3176.2 | 6248.3 |
| critic | $0.03862 | $0.06238 | 8663.4 | 19372.6 |
| planner | $0.06366 | $0.11627 | 24407.5 | 40763.2 |
| reflection | $0.01759 | $0.02190 | 0.0 | 0.0 |
| tools | $0.03345 | $0.03721 | 5648.1 | 14285.4 |

## Marginal costs

| Unit | Cost |
|---|---:|
| reflection iteration | $0.00879 |
| plan step | $0.01384 |
| critic role | $0.00791 |
| graph read | $0.00000 |
| orchestrator worker | $0.00000 |

## Cost per point

| Stage | Δ score | Δ cost/item | Cost/point | Verdict |
|---|---:|---:|---:|---|
| Reflection (M2) | +0.0667 | $+0.01039 | undefined | undefined — within noise |
| Tool use (M3) | -0.0619 | $+0.01587 | undefined | undefined — within noise |
| Planning (M4) | -0.0398 | $+0.03020 | undefined | undefined — within noise |
| Generator–critic (M5) | +0.1564 | $-0.01014 | undefined | undefined — non-comparable scope |
| Review panel (M5) | +0.0000 | $-0.01909 | undefined | undefined — non-comparable scope |
| Gated chain (M6) | -0.1214 | $-0.03443 | undefined | undefined — non-comparable scope |
| Routed (M6) | -0.0100 | $+0.03874 | undefined | undefined — non-comparable scope |
| Orchestrator (M6) | +0.1314 | $-0.00432 | undefined | undefined — non-comparable scope |
| Graph (M9) | +0.0607 | $+0.00000 | undefined | undefined — within noise |
