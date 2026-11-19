# Fixed code-generation task

Implement `build_followup(analysis: dict) -> dict`.

The returned object must contain `action`, `rationale`, and `evidence_count`.

- `page_now`: severity is `SEV-1` and a nonblank recurrence key exists.
- `schedule_review`: severity is `SEV-1` or a nonblank recurrence key exists.
- `monitor`: every other valid case.
- `rationale`: nonblank and mentions the decision inputs.
- `evidence_count`: number of evidence strings.
- Valid severities are `SEV-1`, `SEV-2`, and `SEV-3`.
- Evidence must be a nonempty list of nonblank strings.
- Invalid inputs raise `ValueError`.

The same task and eight acceptance checks are used for all three runs.
