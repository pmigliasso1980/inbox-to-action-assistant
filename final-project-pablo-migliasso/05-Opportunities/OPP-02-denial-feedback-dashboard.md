# OPP-02: Denial root-cause feedback dashboard

**Department:** Revenue Cycle and Practice Operations
**Source:** WF-R02 and WF-O01
**Primitives:** data analysis, automation
**Verdict:** **GO — implement as a non-AI prerequisite**

## Workflow change

Join the monthly ClearBridge reason-code report to responsible upstream workflow categories, publish the
top recurring causes, and assign one owner and corrective action per cause. Start with structured rules;
do not add a model until unstructured cases prove the need.

## Impact

**5,781 first-pass denials/month projected** include **1,965.5 missing/invalid authorization cases/month
projected**. The dashboard does not promise to remove them; it makes recurrence and ownership measurable.
It also exposes the **2,681-denial/month projected** gap between denials and worked cases.

| Check | Result | Reason |
|---|---|---|
| Rule-based | Yes | Reason codes and ownership mapping are deterministic. |
| Digital/structured input | Yes | ClearBridge export and API already exist. |
| Volume/frequency | Yes | **47,000 claims/month measured**. |
| Stable process | Yes | Monthly denial reporting already runs. |
| Data accessible | Yes | Kestrel exchanges ClearBridge files daily. |

**Impact 4/5; feasibility 5/5; effort 2/5; change difficulty 2/5.** Suggested owner: VP Revenue Cycle,
with Practice Operations accountable for assigned upstream causes.

> “We are a very good team at cleaning up a mess we are not allowed to prevent.”
> — Billing specialist [B3.2]
