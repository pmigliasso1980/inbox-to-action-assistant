# Decision log

| # | Decision | Evidence used | What would change the decision |
|---:|---|---|---|
| 1 | Use Track B and treat Kestrel as a real engagement dossier, not a product brief. | The assignment provides interviews, shadow notes, survey data, systems, and contradictions. | Access to a real Track A client and permission to publish anonymized artifacts. |
| 2 | Prioritize workflow evidence over AI enthusiasm. | Survey use is high, but governance is low and prior pilots lacked baselines. | A production evaluation showing safe, governed, repeatable value. |
| 3 | Map prior authorization, referral intake, and denials in detail. | They have the strongest combination of volume, time, handoffs, and source evidence. | Better shadow evidence from credentialing or scheduling. |
| 4 | Label numbers as measured, observed, reported, projected, assessed, or proposed. | The dossier mixes sources and contains contradictions. | Nothing; source labeling is a permanent reporting rule. |
| 5 | Rank referral intake first. | Bounded scope, observable quality, 377.6–485.5 projected monthly hours, and RightFax API access. | A measured baseline showing negligible work or unacceptable document risk. |
| 6 | Make denial reconciliation a non-AI prerequisite. | 5,781 projected denials and 3,100 measured worked denials do not reconcile. | A validated shared definition and reconciled source table already in production. |
| 7 | Keep humans responsible for referral routing. | Missing data, handwriting, contradictions, and patient harm make autonomy inappropriate. | A separately governed clinical validation program with evidence sufficient for a new risk decision. |
| 8 | Use a staged read-only pilot. | Caregate write approval takes 8–12 reported weeks and is unnecessary to test extraction. | A proven sandbox write path with equivalent controls and easy rollback. |
| 9 | Freeze evaluation thresholds before production. | Prior pilots lacked success metrics; post-hoc thresholds invite self-deception. | Thresholds may be changed only before testing, with owner and risk approval. |
| 10 | Treat the recording as candidate-owned work. | The assessment explicitly requires delivery, and a generated impersonation would misrepresent performance. | The course explicitly accepts a written script instead of a recording. |

## Not-do decisions

1. Do not deploy an autonomous patient-balance agent; harm, compliance, and reputational risks exceed current controls.
2. Do not claim all 377.6–485.5 projected referral hours as savings; they are addressable workload, not removable effort.
3. Do not use consumer AI accounts with PHI or begin before the data path is approved.
4. Do not automate prior-authorization portal actions in the first pilot; integration and measurement readiness are insufficient.
