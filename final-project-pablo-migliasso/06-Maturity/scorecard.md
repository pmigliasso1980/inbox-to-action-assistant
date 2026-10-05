# AI maturity scorecard

The scorecard predicts adoption blockers; it does not grade the organization. Scores use a five-level
scale with half points. Claims come from interviews/surveys; evidence comes from observed work, artifacts,
or system counts.

## Overall assessment

| Dimension | Score | What is true now |
|---|---:|---|
| Leadership and strategy | 2.5 | A board-level cost problem, sponsor, and budget exist, but no accountable internal AI owner or measured pilot method exists. |
| People and skills | 2.0 | Staff experiment independently; evaluation skill, training, and shared practice remain weak. |
| Data | 2.5 | Core systems expose useful data, while key workflows rely on PDFs, desktop spreadsheets, and undocumented joins. |
| Tools and technology | 2.0 | Enterprise systems and APIs exist, but administrative AI access is fragmented and mostly unsanctioned. |
| Governance and risk | 1.5 | Compliance knows the required controls, but policy, BAA coverage, and accountable ownership are absent. |
| Adoption and usage | 1.5 | Small pockets use AI; one pilot fragmented without a baseline, and regular administrative use is not sanctioned. |

## Leadership and strategy — 2.5

Kestrel has an explicit business problem: cost to collect is **4.1% reported** versus a **3.2% reported
peer median**, days in accounts receivable rose from **41 to 46 reported**, and the board is challenging
administrative growth [B1.2]. The COO sponsors discovery and confirms budget exists, but cannot name an
internal AI owner [B3.3].

Evidence:

- **Evidence:** signed partner letter names cost and collection trends [B1.2].
- **Claim:** COO says budget exists and ownership is the constraint [B3.3].
- **Evidence:** 2024 pilot had no baseline or success metric [B1.3].

To reach 3: name one accountable owner and approve written success metrics and decision rights for a pilot.

## People and skills — 2.0

### Four fluencies

| Fluency | Assessment | Evidence |
|---|---|---|
| Delegation | 2.5 | Frontline staff clearly separate typing/chasing from judgment [B4, B8], but AI use remains ad hoc. |
| Description | 2.0 | Text drafting dominates reported use; no evidence shows consistent context or constraint setting [B2]. |
| Discernment | 1.5 | One specialist nearly used a fabricated policy citation and caught it only by format [B3.2]. |
| Diligence | 1.5 | Personal accounts are common and policy is absent; staff lack a shared verification method [B2, B6]. |

Evidence:

- **Evidence:** **153 responses measured**, with **68% reported self-rating 4–5** and only **37% reported**
  finding output usable with light editing [B2].
- **Claim:** **6% reported** receiving AI training [B2].
- **Evidence:** workshop participants expressed surprise that AI can write spreadsheet formulas [B5].

To reach 3: publish allowed-use guidance, train pilot users on verification, and assess discernment with
realistic domain examples rather than self-rating.

## Data — 2.5

| Workflow cluster | Score | Basis |
|---|---:|---|
| Claims and denials | 3.5 | ClearBridge data is structured, exportable, and already exchanged daily; reason-code reports exist [B6, B7]. |
| Referral intake | 2.5 | RightFax PDFs are accessible by API, but inputs are unstructured and the error baseline is absent [B4.2, B6, B10]. |
| Prior authorization | 1.5 | Caregate has a read API, yet active status and payer rules live in personal spreadsheets and portals [B4.1, B6, B7]. |
| Credentialing | 2.0 | Shared tracker exists; sensitive documents and portal status are fragmented; no shadowing was completed [B3.3, B10]. |
| Patient Growth reporting | 3.0 | Caregate, HubSpot, and target data are digital, but reconciliation depends on a personal spreadsheet [B3.3]. |

Evidence:

- **Evidence:** Caregate read API and ClearBridge API are licensed and in use [B6].
- **Evidence:** a **431-row measured** personal authorization tracker and **900-row reported** fax lookup
  contain operational logic outside governed systems [B4, B7].

To reach 3: establish governed shared datasets for authorization status and referral reference data, then
measure completeness and error rates.

## Tools and technology — 2.0

Kestrel has capable operational platforms and Microsoft 365, but workflows bridge seven payer portals,
fax, SharePoint, Access, and spreadsheets. Four Copilot licences exist in Patient Growth, while no
administrative AI platform is sanctioned [B1.5, B3.3, B6].

Evidence:

- **Evidence:** systems inventory and API review [B1.5, B6].
- **Claim:** IT knows four Practice Operations Access databases and assumes more exist [B6].
- **Evidence:** personally maintained spreadsheets perform workflow-system functions [B4, B7].

To reach 3: inventory shadow systems, approve one PHI-capable pilot environment, and document integration
ownership and service levels.

## Governance and risk — 1.5

No AI usage policy or BAA with a general-purpose AI vendor exists. Compliance nevertheless has clear
requirements: minimum necessary data, named accountability, audit trail, risk assessment, and human review
for patient or claim impact [B6]. The previous scribe pilot did follow the BAA process.

Evidence:

- **Evidence:** no policy arrived in documentation [B1.7].
- **Claim from accountable officer:** no PHI may enter a general AI tool today; approval requires **six to
  eight weeks reported** [B6].
- **Evidence:** **71% of surveyed AI users reported** personal-account use [B2].

To reach 2: publish interim rules, name an approver, and approve a defined PHI data flow with audit and
human-review controls.

## Adoption and usage — 1.5

AI adoption is isolated. **12 of 40 clinicians reported** still use the scribe daily; **28 reported**
stopped within six weeks, and no baseline existed. Survey AI users are mostly occasional, while one Patient
Growth team uses Copilot in a repeatable report workflow [B1.3, B2, B3.3].

Evidence:

- **Evidence:** pilot participation counts and absence of measurement [B1.3].
- **Claim:** **9% of surveyed AI users reported** daily use and **19% reported** weekly use [B2].
- **Evidence:** four licences support a real monthly narrative workflow [B3.3].

To reach 2: operate one sanctioned administrative pilot with trained users, usage measurement, and a named
feedback owner.

## Self-report versus observed gap

The survey suggests confidence: **68% of 153 respondents reported** digital literacy of 4 or 5, and **51%
reported** using AI for work [B2]. Observed work across **255 minutes measured** of shadowing showed no AI
use in authorization or referral intake, and workshop participants were surprised by basic scripting
capability [B4, B5]. The gap is not dishonesty; it means occasional consumer-style usage does not equal
operational fluency, especially in discernment and diligence.

## Adoption blockers

1. **PHI has no approved AI destination.** Any referral or authorization pilot would fail security review
   today because no general-purpose vendor BAA or risk assessment exists. Smallest removal: compliance and
   IT approve one bounded data flow and vendor in **six to eight weeks reported** [B6].
2. **No client-side owner can make cross-team decisions.** Referral, authorization, denials, IT, and
   compliance must change together; without an owner, access and policy decisions stall. Smallest removal:
   COO names one accountable pilot owner with delegated decision rights.
3. **Two safety baselines are missing.** Referral keying error and authorization-linkage failure rates are
   unknown, so a pilot could look faster while worsening claims or patient routing. Smallest removal: run a
   four-week double-review sample before go/no-go.
