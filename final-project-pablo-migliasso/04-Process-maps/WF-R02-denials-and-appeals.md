# WF-R02: Denial review and appeal

**Owner:** VP Revenue Cycle. **Trigger:** ClearBridge places a denied claim in the overnight Caregate queue.

## Process map

| Step | Actor | System | Work and output | Work time | Wait/elapsed time | Pain or workaround |
|---:|---|---|---|---|---|---|
| 1 | Billing specialist | Caregate/ClearBridge | Open next denial and inspect reason code | Included below | Queue wait | Queue size hides below-threshold write-offs. |
| 2 | Billing specialist | Caregate | Check whether authorization exists | **5 min reported** | None | **Pain:** auth may exist but not be attached. |
| 3 | Billing specialist | Email/coordinator | Ask prior-auth team when record is absent | Minutes unknown | **1–2 days reported** | **Pain at step 3:** cross-team wait and no shared status source. |
| 4 | Billing specialist | SharePoint | Find a similar prior appeal | Included below | Search duration unknown | **Workaround:** **1,400 reported** unindexed letters, no owner. |
| 5 | Billing specialist | Caregate/SharePoint | Assemble documentation and draft appeal | **40 min reported** for standard appeal | None | Risk of stale or fabricated payer-policy language. |
| 6 | Billing specialist | Portal/fax | Submit appeal | Included above | **30–45 days reported** | Payer-specific channel and long elapsed time. |
| 7 | Revenue Cycle | ClearBridge | Record outcome and continue queue | Unknown | Payer decision | No upstream feedback loop closes recurring causes. |

## Inputs and outputs

Inputs: denial reason, claim, authorization evidence, clinical documentation, payer policy, and prior appeals.
Outputs: corrected claim, appeal package, write-off, or documented final denial.

## Exceptions

- Authorization existed but was not linked.
- Authorization never existed.
- Medical-necessity denial requires case-specific clinical judgment.
- Claim falls below the work threshold and is written off without team review.
- Precedent letter contains stale or incorrect payer policy.

## Baseline and arithmetic

- **47,000 claims/month measured** × **12.3% measured first-pass denial rate** = **5,781 denials/month
  projected** [B9].
- **3,100 denials/month measured** are worked. The difference, 5,781 − 3,100 = **2,681/month projected**,
  is written off below a dollar threshold according to IT [B9].
- Minimum first review = 3,100 × **5 minutes reported** ÷ 60 = **258.3 hours/month projected**.
- A standard appeal requires **40 minutes reported**; the appeal share is unknown, so total appeal hours
  cannot be calculated honestly.
- **34% measured** carry “missing or invalid prior authorization.” Applied to all first-pass denials, that
  is 5,781 × 0.34 = **1,965.5 cases/month projected**. The rate where authorization existed but was not
  attached remains unknown.
- Specialists report **15–20 denials/day each** across **11 people reported**. At **21.67 workdays/month
  projected**, that implies **3,575–4,767 touches/month projected**, which conflicts with **3,100 unique
  denials/month measured**. We preserve both rather than averaging them.

Work time has a **258.3-hour/month projected minimum**, excluding appeal assembly. Elapsed time includes
**one to two days reported** waiting for authorization evidence and **30–45 days reported** for payer appeal
decisions.

Sources: B3.2, B7, B9, B10. Revenue Cycle was not shadowed, so all step times are claims [B10].
