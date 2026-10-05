# Kestrel Health Group client brief

## What Kestrel does and how margin moves

Kestrel is a physician-owned multi-specialty group operating outpatient care across North Carolina and
southern Virginia. It earns primarily through reimbursement for clinical services, so margin improves
when claims are accepted promptly and clinicians can deliver billable care without administrative
delay. The central margin pressure is revenue-cycle friction: net patient revenue is **$412 million
(reported)**, cost to collect is **4.1% (reported)** against a **3.2% peer median (reported)**, days in
accounts receivable rose from **41 to 46 (reported)**, and first-pass claim acceptance fell below
**88% (reported)** [B1.2].

Kestrel employs **1,140 people (reported)** overall and **473 people (reported)** in the four departments
in scope [project brief; B1.6]. It added **63 administrative staff (reported)** while adding **11
clinicians (reported)** over two years [B1.2]. Leadership therefore wants a factual account of recurring
administrative work and a ranked set of changes that reduce rework without weakening patient or claim
controls.

## Relationship with AI

Kestrel ran an ambient-scribe pilot with **40 clinicians (reported)** in 2024. **12 clinicians
(reported)** still use it daily and **28 (reported)** stopped within six weeks; no baseline was captured
[B1.3]. Administrative staff have no sanctioned AI tool [B1.3, B6]. The survey found **51% of 153
respondents (reported)** had tried AI for work, and **71% of those users (reported)** used personal
accounts [B2]. Four Copilot licences exist in Patient Growth [B3.3].

Compliance sets the binding condition: no Business Associate Agreement exists with a general-purpose AI
vendor, so protected health information cannot be sent to one today. A PHI-capable tool requires a BAA
and risk assessment, taking **six to eight weeks (reported)** at minimum [B6].

## Business vocabulary

The working vocabulary is defined in [`vocabulary.md`](vocabulary.md). The most consequential terms are
cost to collect, first-pass acceptance, prior authorization, denial, appeal, and BAA because they connect
workflow steps to margin and deployment feasibility.

## Key people and influence

- The COO sponsors discovery, controls access to budget, and wants numbers rather than a strategy deck.
- The CEO links the work to physician burden and patient access.
- The VP Revenue Cycle owns cost to collect and days in accounts receivable.
- The Director of Practice Operations owns the largest in-scope department and the two observed workflows.
- The Chief Compliance Officer controls whether any PHI-bearing pilot may proceed.
- The Director of IT controls system access, security review, service accounts, and integration lead time.
- Frontline coordinators hold undocumented operational knowledge and are likely pilot champions.

The detailed influence map is in [`../02-Stakeholders/stakeholder-map.md`](../02-Stakeholders/stakeholder-map.md).

## Documentation and systems

Kestrel supplied a current org chart, a systems inventory, an **84-page billing manual dated 2021
(reported)**, and a 2023 front-desk guide [B1.7]. It supplied no prior-authorization procedure, no
referral-intake procedure, no complete credentialing procedure, and no AI usage policy [B1.7].

Core systems include Caregate, ClearBridge, RightFax/eFax, seven payer portals, SharePoint/OneDrive,
Microsoft 365, Sage Intacct, Paylink, HubSpot, Genesys, and an unknown number of Access databases [B1.5].
Caregate has a licensed read API available through a service account in **about two weeks (reported)**;
write access requires vendor approval estimated at **eight to twelve weeks (reported)** [B6]. RightFax
has an API that IT estimates could be enabled in **one day (reported)** [B6].

## Engagement scope and sponsor intent

The four-week remote discovery covers Revenue Cycle, Practice Operations, People and Talent, and Patient
Growth [B1.3]. The sponsor explicitly wants workflow evidence, costed recommendations, and permission to
recommend fewer hires or no new tool. He does not want a generic AI strategy deck or vendor selection.

## Open questions and contradictions

| Question or tension | Why it matters | Resolution path |
|---|---|---|
| **3,100 denials worked per month (measured)** versus **5,781 first-pass denials per month (projected from measured counts)** | The **2,681-case projected gap** is written off below threshold, so queue size understates failure cost. | Reconcile write-off dollars and reason codes with Finance and ClearBridge. |
| Staff report **15–20 denials per day each (reported)** across **11 people (reported)**, implying **3,575–4,767 cases per 21.67-day month (projected)**, versus **3,100 measured** | Productivity and staffing conclusions change materially. | Sample one month of individual completions and distinguish touches from unique denials. |
| Missing/invalid prior authorization is **34% of denials (measured)**, but the share where an authorization existed and was merely unattached is unknown | The remedy could be linkage, submission quality, or both. | Manually sample at least 100 such denials before designing automation. |
| Referral keying error rate is unknown | Time savings alone cannot prove a safe pilot. | Add double-entry audit on a synthetic/approved sample and create an error baseline. |
| Prior-authorization phone versus portal chase mix is unknown | Phone automation feasibility and true chase hours cannot be estimated. | Tag chase channel for four weeks in a shared tracker. |
| Central Scheduling, **70 people (reported)**, was not covered | This is a major coverage and confidence gap. | Interview its lead and shadow one scheduling shift before final investment approval. |

## Source boundary

All evidence comes from fictional dossier parts B1–B10. No patient content, employee performance data, or
real organization data appears in this submission.
