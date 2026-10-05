# OPP-04: Prior authorization chase digest

**Department:** Practice Operations
**Source:** WF-O01
**Primitives:** automation, data analysis
**Verdict:** **AUGMENT — strategic, not first**

## Workflow change

Create a governed shared authorization worklist, ingest available payer status feeds, and present overnight
changes and exceptions. Coordinators handle phone-only payers, clinical sufficiency, and final submission.

## Impact

At least **1,464 chase events/month projected** create **103.7 hours/month projected** of portal work as a
lower bound; phone cases are longer and the channel mix is unknown. Patient delay matters more than hours,
but no average authorization turnaround baseline exists.

| Check | Result | Reason |
|---|---|---|
| Rule-based | Partial | Chase dates and status deltas are rule-based; clinical support is not. |
| Digital/structured input | Weak | Status spans personal tracker, portals, phone, and fax. |
| Volume/frequency | Yes | **61% of 2,400 requests/month measured** require chase. |
| Stable process | Yes | Chasing is daily and long-standing. |
| Data accessible | Weak | Seven payer portals lack Kestrel APIs; only three have status API via an unpurchased product. |

**Impact 5/5; feasibility 2/5; effort 5/5; change difficulty 3/5.** Suggested owner: Director of Practice
Operations. Begin with shared visibility and data collection, not autonomous payer interaction.

> “If something did the chasing and just told me what changed overnight, I would get my afternoons back.”
> — Prior authorization coordinator [B8]
