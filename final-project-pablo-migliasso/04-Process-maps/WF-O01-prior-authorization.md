# WF-O01: Prior authorization submission and chase

**Owner:** Director of Practice Operations. **Operational knowledge holder:** prior authorization
coordinator. **Trigger:** a Caregate order for a service that may require payer authorization.

## Process map

| Step | Actor | System | Work and output | Work time | Wait/elapsed time | Pain or workaround |
|---:|---|---|---|---|---|---|
| 1 | Coordinator | Caregate | Pick order and identify payer, plan, procedure | Included below | None observed | Payer/plan rules must be inferred across sources. |
| 2 | Coordinator | Policy PDF/knowledge | Decide whether authorization is required | Included below | None observed | **Pain:** PDF may be outdated; rule changes surface through denials. |
| 3 | Coordinator | Caregate | Assemble patient, code, and clinical documentation | Included below | If incomplete, **1 day–1 week reported** | **Pain at step 3:** about **25% reported** require clinic follow-up. |
| 4 | Coordinator | Portal/RightFax | Submit request | Completed cases **14, 17, 19 min measured end-to-end** | Payer decision time unknown | Portal formatting and fax receipt fail silently. |
| 5 | Coordinator | Personal Excel | Add status and chase date | Included in observation | Usually five business days before chase | **Workaround:** private tracker is the workflow system. |
| 6 | Coordinator | Portal/phone | Check status and re-submit when missing | Portal cases **3–6 min measured**; phone example **21 min measured** | Phone example included **13 min measured hold** | **Pain:** no usable portal for three of seven payers, reported. |
| 7 | Coordinator | Caregate | Attach approved authorization to order | Included in chase observation | Until approval | **Pain:** unattached authorizations later appear as denials. |
| 8 | Scheduler/front desk | Phone/coordinator | Ask status when patient is waiting | **4 min measured example** | Patient may wait for care | **Workaround:** approximately **10 interruptions/day across team reported**. |

## Inputs and outputs

Inputs: Caregate order, patient coverage, CPT code, payer rules, and clinical evidence. Outputs: payer
submission, status history, authorization attached to the order, or a documented denial/exception.

## Exceptions

- Missing clinical note, code, or measurement returns to the clinic.
- Payer reports that a faxed request was never received.
- Portal rejects formatting without a legible reason.
- Payer rule or plan requirement changed without notification.
- Urgent scheduling request requires immediate status search.

## Baseline and arithmetic

- **2,400 requests/month measured** [B9].
- Three fully completed new requests took **19, 14, and 17 minutes measured**, a **16.7-minute projected
  sample mean**. Monthly new-request work = 2,400 × 16.7 ÷ 60 = **668 hours/month projected**.
- **61% measured** require at least one chase: 2,400 × 0.61 = **1,464 chases/month projected**.
- Eight portal chase rows took approximately **34 minutes measured** as a batch, or **4.25 minutes
  projected per portal chase**. A lower-bound chase workload = 1,464 × 4.25 ÷ 60 = **103.7 hours/month
  projected**. It excludes additional chases and longer phone cases, so it is not a total.
- Lower-bound combined work = 668 + 103.7 = **771.7 hours/month projected**.
- **18% measured** are initially denied, but this must not be added as a rework multiplier because denial
  work overlaps WF-R02 and would double count.

Work time is at least **771.7 hours/month projected**. Elapsed time is not supported as one average; clinic
waits range from **one day to one week reported**, and payer decision time is absent.

Sources: B3.1, B4.1, B9. Sample sizes and lower-bound limitations are explicit.
