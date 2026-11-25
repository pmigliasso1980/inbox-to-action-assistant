# Independent evaluation results

The evaluator ran as a separate process and exercised the public JSON CLI
without importing either component or using the implementer's unit assertions.
Its expected values came from the sprint contract. This was an automated
black-box evaluation session authored within the lab, with no separate human
reviewer or paid model call.

Reproduce from the repository root:

```bash
python3 -m unittest discover -s experiments/boundary_e2e -v
python3 experiments/boundary_e2e/evaluate.py
```

The unit command exited 0 with four passing checks, two per component. The
evaluator exited 1 as expected on the intentionally flawed implementation.
Each CLI subprocess exited 0.

```text
{"case": "immediate", "request": {"delay_minutes": 0, "now_epoch_seconds": 1000}, "expected": 1000, "observed": {"due_at_epoch_seconds": 1000}, "app_exit_code": 0, "passed": true}
{"case": "one_minute", "request": {"delay_minutes": 1, "now_epoch_seconds": 1000}, "expected": 1060, "observed": {"due_at_epoch_seconds": 1001}, "app_exit_code": 0, "passed": false}
{"case": "five_minutes", "request": {"delay_minutes": 5, "now_epoch_seconds": 1000}, "expected": 1300, "observed": {"due_at_epoch_seconds": 1005}, "app_exit_code": 0, "passed": false}
Contract checks: 1/3 passed
```

## Verdict

**Feature acceptance failed.** Public CLI contract **C** (1/3), local
component checks **A** (4/4), reproducibility and diagnosis **A** (commands,
exit statuses, case outputs, and boundary diagnosis recorded).

At the five-minute boundary the producer sends `{"delay_seconds": 5}`;
the wire contract requires 300. The consumer correctly adds the received
seconds to the clock, so it returns 1005 instead of 1300. The producer's
shape assertion accepts the incorrect packet and the consumer test supplies
a valid handcrafted packet. Zero passes because its value is identical in
both units. The one- and five-minute cases reveal the missing conversion.
The repair would multiply minutes by 60 at the producer boundary and add a
producer assertion for the exact wire value.
