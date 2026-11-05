# Lab 4.2 report — replanning under failure

## Part 1 — preserving successful work

Each candidate received a forced first `read_code` failure. Both configurations used the same five frozen items, bounds, tools, and synthesis; only prior-artifact visibility changed.

| Metric | Naive | Preserving |
|---|---:|---:|
| Mean F1 | 0.6143 | **0.6810** |
| Total tokens | **48,008** | 55,104 |
| Total cost | **$0.475280** | $0.520940 |
| Mean steps | **5.6** | 6.6 |
| Duplicated successful executions | 1 | **0** |
| Instrumented tool-side-effect count | **17** | 18 |
| Escalation rate | 40% | **0%** |
| Items above total-step bound | 0 | 0 |

Preservation eliminated the one measured duplicate, so **0% of preserving work versus 3.57% (1/28) of naive executed steps** was duplicated. It did not save tokens in this sample: preserving spent 7,096 more tokens and $0.04566 more because its generated replans were longer and it avoided early escalation. This is an honest counterexample to “preserving is always cheaper”; its value here was higher completion/quality and no repeated work, not lower spend.

For item 006, the naive replan received zero prior artifacts and again began with `s1 read_code → notify_source_lines`. The preserving replan received five bounded artifacts and reduced the remaining work to evidence-specific synthesis steps (`missing_await_finding`, `timeout_and_status_finding`, `final_defect_report`). No duplicated step produced a conflicting second result in the controlled data; nevertheless, the naive repeated read is a correctness hazard because a mutable source could differ between reads.

## Part 2 — escalation threshold sweep

Three items had persistent `read_code` failure; two had one transient failure and then success. Later thresholds were allowed matching replan budgets while retaining the ten-step cap.

| Threshold | Mean F1 | Cost | Mean steps | Escalation rate | Resolved after failure count |
|---:|---:|---:|---:|---:|---|
| 1 | **0.5143** | **$0.128290** | **1.0** | 100% | none; transient cases escalated too early |
| 2 | 0.4810 | $0.286330 | 3.4 | 60% | 2 items after one failure |
| 3 | **0.5143** | $0.493980 | 5.0 | 60% | same 2 after one failure |
| 5 | 0.4810 | $0.722495 | 7.8 | 20% | 2 after one; 2 route-arounds after 3–4 failures |

No successful transient recovery required attempt 3 or later: **0%**. Threshold 1 unnecessarily escalated both transient cases. Threshold 2 recovered both and bounded persistent failures for $0.28633. Thresholds 3 and 5 added $0.20765 and $0.43617 respectively over threshold 2 without quality lift beyond the 0.0667 noise floor. The knee is therefore **two strikes**, which is the recommended threshold.

The apparent late “resolutions” at threshold 5 were planner route-arounds, not a primary tool recovering; they cost substantially more and did not raise aggregate F1. This data supports the two-strikes rule for this task.

## Part 3 — escalation quality

The five threshold-1 outputs were inspected. All five:

- populated structured `failed` and `blocked_by` fields;
- explicitly identified missing tool-verified source evidence;
- avoided presenting that evidence as successfully retrieved; and
- made the next human action clear: restore or retry `read_code` verification.

Rates were 5/5 for explicit missing work, 5/5 for avoiding hidden dependency claims, and 5/5 for a visible next action. Findings synthesized from the source embedded in the immutable objective were labelled as such. No silent synthesis-around-gap defect was found, so no post-run prompt repair was needed.

Complete controlled metrics and the five assessments are in `runs/replanning/summary.json`; per-item plans and outputs remain in the named controlled directories.
