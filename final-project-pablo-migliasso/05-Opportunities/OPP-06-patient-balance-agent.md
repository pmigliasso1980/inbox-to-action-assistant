# OPP-06: Autonomous patient-balance conversation agent

**Department:** Revenue Cycle
**Source:** WF-R03
**Primitives:** conversational automation
**Verdict:** **NO GO**

## Proposed change rejected

An autonomous agent would contact patients, negotiate payment plans, and decide how long to continue a
financial-hardship conversation. This would place sensitive financial and patient-facing judgment inside
an unproven automated channel.

## Impact and evidence limit

Six staff are reported to perform this work, and volume is described only as high [B3.3]. No case volume,
outcome baseline, complaint rate, or hardship-policy decision logic is supplied, so no quantitative impact
claim is possible.

| Check | Result | Reason |
|---|---|---|
| Rule-based | No after opening script | Conversation becomes judgment-intensive after about **30 seconds reported**. |
| Digital/structured input | Partial | Balance data is structured; emotional and hardship context is not. |
| Volume/frequency | Claimed high | No measured count was provided. |
| Stable process | No | Staff adapt or stop based on distress and context. |
| Data accessible | Conditional | PHI and financial context require strict controls; no approved AI environment exists. |

**Impact 2/5; feasibility 1/5; effort 5/5; change difficulty 5/5.** Do not pilot autonomous conversations.
If leadership wants improvement, first analyze call reasons and strengthen agent-assist scripts without
automating the human relationship. Suggested owner for any future discovery: Patient Balance manager.

> “Half this job is knowing when to stop asking.”
> — Patient balance specialist [B3.3]
