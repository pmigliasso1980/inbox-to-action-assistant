# Failure Analysis — Five Worst Final Items

The five worst items are incidents 016–020. Each scores 0.80; the cause,
severity, owner, and recurrence are correct, but remediation omits the required
service-specific load-test verification.

| Item | What failed | Component/artifact | Course failure mode | Next action and expected cost |
|---|---|---|---|---|
| 016 checkout | Generic backpressure fix lacks a checkout load test | `runs/graph.json`, record 16 | Underspecified completion criterion | Add remediation policy table and one deterministic check; ~$0 runtime |
| 017 catalog | Cache fix lacks version-transition load test | record 17 | Evaluator coverage gap | Add a rubric criterion for verification evidence; one local pass |
| 018 notifications | Queue fix lacks burst-load validation | record 18 | Tool result is relevant but incomplete | Extend runbook tool with validation requirements; one lookup |
| 019 identity | Certificate fix lacks renewal-failure exercise | record 19 | Happy-path bias | Add an expiry/renewal failure-injection case; no model call |
| 020 search | Timeout fix lacks dependency load test | record 20 | Plan omitted proof of success | Add a typed `verification_method`; one schema migration |

The graph did not cause these failures. It correctly retrieved recurrence, but
durable knowledge cannot compensate for an output contract that treats
verification detail as part of an unstructured remediation string. The next
iteration should make verification a separate scored field rather than adding
another agent.
