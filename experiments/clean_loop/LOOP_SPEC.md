# Loop specification

## Goal and trigger

Prepare a Markdown index snippet for two recent lab reports as a repeatable
version of the manual link check after lab updates. Invoke the loop on demand
from the repository root. This exercise assumes a twice-weekly cadence for
the chore. Actual historical frequency was not measured.

## Loop type and primitives

A bounded generate–evaluate–retry loop. A pinned Git snapshot supplies
reproducible inputs and a disposable directory keeps the run isolated.
A deterministic generator first looks for conventional README files, then
widens its discovery to results and comparison files on retry. Separate
processes and a JSON handoff let the evaluator check the proposal without
importing generator code. A separately maintained manifest defines coverage,
and filesystem checks verify the expected targets exist. A digest ties each
verdict to its candidate.

## Verification and stopping condition

The evaluator checks exact target coverage, existence, line format, and
duplicate targets. Its exit status and JSON verdict must agree. Stop on
the first accepted candidate or after two attempts. A crashed or timed-out
process stops the run. The coordinator checks temporary directory removal
and confirms Git status is unchanged. The accepted snippet requires human
review before any root README edit.

The parser covers the generated list-item format. Link labels, report
contents, remote URLs, and links elsewhere in the repository require
separate review.
