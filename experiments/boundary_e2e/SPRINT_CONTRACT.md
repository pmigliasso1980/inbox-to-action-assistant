# Sprint contract · inbox review reminder

Deliver a toy CLI that takes an inbox review delay in minutes and returns
the due time in Unix epoch seconds. The producer translates the request to
a queue packet. The consumer schedules that packet against a supplied clock.

## Interfaces and acceptance

- Input JSON on stdin contains a nonnegative integer `delay_minutes` and
  an integer `now_epoch_seconds`. Output JSON on stdout contains
  `due_at_epoch_seconds = now_epoch_seconds + 60 × delay_minutes`.
- The internal queue packet contains a nonnegative integer `delay_seconds`.
  A five-minute input must produce 300 seconds on the wire.
- Each component's local tests must pass. The independent harness runs the
  CLI as a subprocess and compares complete output objects to fixed
  contract examples at a clock value of 1000. Delays of 0, 1, and 5 minutes
  must yield 1000, 1060, and 1300 respectively for an acceptance pass.
- The lab succeeds when the flawed revision passes its unit suite and the
  harness rejects it with concrete expected and observed values.

## Exclusions

Production inbox code, persistence, real clocks, network services,
authentication, and real reminders are outside scope. The intentional
defect is retained only in this isolated lab.
