# Workflow inventory

All quantities retain their dossier status. “Unknown” means the dossier does not support a number.

| ID | Workflow | Department | Trigger and frequency | Time per run | People | Systems | Pain | Source |
|---|---|---|---|---|---:|---|---:|---|
| WF-O01 | Prior authorization submission and chase | Practice Operations | Order enters Caregate; **2,400/month measured** | New request **14–19 min measured** in three completed observations; chase varies | **14 reported** | Caregate, payer portals, phone, RightFax, Excel | 5/5 | B3.1, B4.1, B9 |
| WF-O02 | Referral intake | Practice Operations | Referral arrives; **5,800/month measured**, **62% fax measured** | Fax cases **6.3–8.1 min projected observed range** | **9 reported** | RightFax, Caregate, lookup spreadsheet, phone | 5/5 | B3.3, B4.2, B9 |
| WF-O03 | Central scheduling | Practice Operations | Appointment request; frequency unknown | Unknown | **70 reported** | Caregate, Genesys | Unknown | B10 coverage gap |
| WF-O04 | Medical-record release | Practice Operations | Release request; frequency unknown | Unknown | Unknown | Caregate, fax, SharePoint | Unknown | B1.6 only |
| WF-R01 | Claim submission and billing | Revenue Cycle | Care delivered; **47,000 claims/month measured** | Unknown | Unknown | Caregate, ClearBridge | 4/5 | B1.2, B9 |
| WF-R02 | Denial review and appeal | Revenue Cycle | Claim denial; **5,781/month projected**, **3,100 worked/month measured** | Initial lookup **5 min reported**; standard appeal **40 min reported** | **11 reported** | Caregate, ClearBridge, SharePoint, payer portals, fax | 5/5 | B3.2, B9 |
| WF-R03 | Patient balance outreach | Revenue Cycle | Outstanding balance; volume described as high, not quantified | Unknown | **6 reported** | Caregate, Genesys | 4/5 | B3.3 |
| WF-R04 | Revenue-cycle reporting | Revenue Cycle | Monthly reporting; frequency reported | Unknown | Unknown | ClearBridge, Caregate, Excel | 3/5 | B1.6, B7 |
| WF-P01 | New-provider payer enrollment | People and Talent | New clinician; **35/quarter measured** | **40 min per payer reported**, approximately **14 payers reported** | **4 reported** across credentialing | Payer portals, SharePoint, spreadsheet | 5/5 | B3.3, B9 |
| WF-P02 | Recredentialing | People and Talent | Renewal cycle; **60/quarter measured** | Unknown | **4 reported** across credentialing | Payer portals, SharePoint, spreadsheet | 4/5 | B3.3, B9 |
| WF-P03 | Recruiting | People and Talent | Position opens; frequency unknown | Unknown | Unknown | Paylink, Microsoft 365 | Unknown | B1.5–B1.6 |
| WF-G01 | Monthly practice-growth report | Patient Growth | Month end; **monthly reported** | **21 team-hours/month reported** | **3 reported** | Caregate, HubSpot, Excel, Copilot | 3/5 | B3.3 |
| WF-G02 | Community and referral relations | Patient Growth | Campaign/event cycle; frequency unknown | Unknown | Unknown | HubSpot, Microsoft 365 | Unknown | B1.6 |

Pain ratings are analyst judgments on a five-point scale based on delay, rework, risk, and single-person
dependency. They are not client measurements.

## Deep-dive choice

WF-O01, WF-O02, and WF-R02 were selected because they form a causal chain: referral quality affects
authorization, and authorization failures create denials. They also combine two observed workflows with
one financially material downstream workflow, exposing where one team’s workaround becomes another
team’s rework. The main limitation is that Revenue Cycle was interviewed but not shadowed [B10].
