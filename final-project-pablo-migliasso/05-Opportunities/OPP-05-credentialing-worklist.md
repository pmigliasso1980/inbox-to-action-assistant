# OPP-05: Credentialing and enrollment worklist

**Department:** People and Talent
**Source:** WF-P01 and WF-P02
**Primitives:** automation, data analysis
**Verdict:** **GO for process redesign; defer AI**

## Workflow change

Replace the shared spreadsheet with a governed worklist that records payer submissions, follow-up dates,
status, evidence links, and ownership. Add reminders and a daily exception digest. Do not ingest sensitive
credentialing documents into AI during this phase.

## Impact

New enrollment form filling alone equals **35 starts/quarter measured × 14 payers reported × 40 minutes
reported = 326.7 hours/quarter projected**, or **108.9 hours/month projected**. This excludes document
assembly, follow-up, and **60 recredentialing cycles/quarter measured**, whose payer/form counts are unknown.

| Check | Result | Reason |
|---|---|---|
| Rule-based | Yes for worklist | Dates, ownership, and missing statuses are deterministic. |
| Digital/structured input | Partial | Tracker is structured; linked documents are sensitive and variable. |
| Volume/frequency | Yes | **95 total starts/quarter measured** across enrollment and recredentialing. |
| Stable process | Yes | Payer enrollment and follow-up recur for every provider. |
| Data accessible | Weak | Payer portal API access is not documented; workflow was not shadowed. |

**Impact 4/5; feasibility 2/5; effort 4/5; change difficulty 2/5.** Suggested owner: Credentialing Lead,
sponsored by Director of People Operations. Validate the map before investment.

> “I want to know which of the fourteen forms are still sitting there without logging into fourteen websites.”
> — Credentialing lead [B8]
