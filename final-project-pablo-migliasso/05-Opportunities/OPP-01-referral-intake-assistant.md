# OPP-01: Referral intake extraction assistant

**Department:** Practice Operations
**Source:** WF-O02
**Primitives:** document extraction, data analysis
**Verdict:** **AUGMENT — pilot first**

## Workflow change

Retrieve inbound fax PDFs from RightFax, extract candidate referral fields, compare identifiers with
Caregate read data, and present a structured draft. A coordinator verifies every field and retains
specialty, site, and urgency decisions. Initial scope stops before Caregate write integration.

## Impact

**3,596 fax referrals/month projected** × **6.3–8.1 min projected** = **377.6–485.5 staff-hours/month
projected** exposed to redesign [WF-O02 baseline]. This is an addressable-work ceiling, not promised
savings. The error rate is unknown, so quality improvement cannot be claimed before baseline sampling.

## Effort and suitability

| Check | Result | Reason |
|---|---|---|
| Rule-based | Partial | Field extraction is statable; urgency and routing judgment stay human. |
| Digital/structured input | Partial | PDFs are digital but variable, handwritten, cropped, and multiply faxed. |
| Volume/frequency | Yes | **3,596 fax referrals/month projected**. |
| Stable process | Yes | The intake fields and Caregate destination recur daily. |
| Data accessible | Conditional | RightFax API takes **one day reported**; PHI requires BAA/risk review; Caregate write needs **8–12 weeks reported**. |

**Impact 5/5; feasibility 4/5; effort 3/5; change difficulty 2/5.** Users already ask to automate typing
and keep judgment, reducing role threat. Suggested owner: Director of Practice Operations, with IT and
Compliance as gate owners.

> “If it typed it in and I checked it, I could do three times as many and I would still be the one who decides.”
> — Referral intake coordinator [B8]
