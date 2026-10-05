# WF-O02: Referral intake

**Owner:** Director of Practice Operations. **Trigger:** an inbound referral arrives by fax, portal, or post.

## Process map

| Step | Actor | System | Work and output | Work time | Wait/elapsed time | Pain or workaround |
|---:|---|---|---|---|---|---|
| 1 | Coordinator | RightFax/portal | Open referral document | Included below | Queue wait unknown | **62% measured** arrive by fax. |
| 2 | Coordinator | Document | Read demographics, provider, specialty, reason, insurance, urgency | Included below | None observed | **Pain:** degraded and handwritten faxes. |
| 3 | Coordinator | Lookup spreadsheet | Resolve referring provider by fax number when unclear | **3 min measured example** | None observed | **Workaround:** personally maintained **900-row reported** lookup. |
| 4 | Coordinator | Phone | Obtain missing insurance or other fields | Example included **6 min measured hold** | Referring-office response | **Pain at step 4:** missing information. |
| 5 | Coordinator | Caregate | Create referral and key fields | Clean cases **4–7 min measured** | None observed | **Pain:** manual re-keying creates unmeasured error risk. |
| 6 | Coordinator | Caregate | Select specialty/site and assess urgency | Included below | None observed | Human judgment retained; form urgency fields are inconsistent. |
| 7 | Downstream teams | Caregate | Scheduling and authorization consume record | Not observed | Patient waits if misrouted | Keying defects propagate downstream. |

## Inputs and outputs

Inputs: referral PDF or portal record, provider identity, insurance, clinical reason, specialty, and urgency.
Output: structured Caregate referral routed for scheduling and, where relevant, authorization.

## Exceptions

- Illegible, multiply faxed, handwritten, or cropped document.
- Missing insurance or referring-provider identity.
- Patient not found in Caregate.
- Urgency stated inconsistently or only implied in clinical text.
- Conflicting values between referral document and existing record.

## Baseline and arithmetic

- **5,800 referrals/month measured**; **62% measured** arrive by fax [B9]. Fax volume = 5,800 × 0.62 =
  **3,596/month projected**.
- Ten fax cases were observed. Two exact clean cases totaled **10 minutes measured**. Six additional clean
  cases ranged from **4 to 7 minutes measured each**. Two problematic cases took **13 and 16 minutes
  measured**.
- Observed ten-case work range = 10 + (6 × 4 to 6 × 7) + 13 + 16 = **63–81 minutes projected from
  measured bounds**, or **6.3–8.1 minutes/case projected**.
- Monthly fax-intake work = 3,596 × 6.3–8.1 ÷ 60 = **377.6–485.5 hours/month projected**.
- The coordinator reported **about 25% problematic**; the observed sample contained **20% measured**
  problematic cases. The sample is too small to call that a contradiction.
- No error-rate multiplier is applied because the error rate is unknown [B10].

Work time is **377.6–485.5 hours/month projected** for fax referrals only. Elapsed time was not measured;
phone follow-up adds variable waiting and downstream misrouting duration is unknown.

Sources: B3.3, B4.2, B7, B9, B10.
