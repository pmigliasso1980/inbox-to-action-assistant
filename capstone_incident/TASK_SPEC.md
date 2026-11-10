# Task Specification

## Purpose and user

The system assists incident commanders and reliability engineers by converting
a short incident report into a normalized, auditable post-mortem summary. It is
decision support, not an autonomous production-control system.

## Input and output

Input is a strict object containing title, service, occurrence time, and report
text. Output contains primary cause, severity, remediation, confirmed owner,
recurrence key, and evidence. Extra input or output fields are forbidden.

## What good means

Five fields are scored by exact match. A good output identifies the correct
cause and severity, proposes the expected remediation, uses the real ownership
directory rather than guessing, and marks recurrence only when an earlier
session contains the same service–cause relationship.

## Risk and pattern family

Risk is medium: a wrong summary can misroute follow-up work, but the system does
not deploy, page, or modify production. The appropriate family is a gated chain
with read-only tools and human review. Graph memory is a candidate because
recurrence is inherently cross-session. Planning and multi-agent orchestration
require measured justification rather than being defaults.

## Qualification against the five criteria

- **New:** incident analysis, not the course's code-review task.
- **Evaluable:** five exact-match fields scored in code.
- **Non-trivial:** baseline mean is 0.50, far below complete.
- **Entity-bearing:** services, incidents, causes, owners, sources, and claims.
- **Multi-session plausible:** repeated service–cause pairs should improve later
  analyses and are explicitly separated in evaluation.
