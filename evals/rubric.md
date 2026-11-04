# Frozen code-review reflection rubric — version 1.0

## Required qualities

1. **valid_json** [deterministic] — Output parses as the required `{"defects": [...]}` structure and every defect has category, line, severity, and rationale.
2. **required_fields** [deterministic] — Category is in the frozen taxonomy, line is an integer, severity is allowed, and rationale is non-empty.
3. **line_numbers_valid** [deterministic] — Every cited line is between 1 and the number of lines in the supplied snippet.
4. **no_duplicate_findings** [deterministic] — No two findings share the same normalized category and line.
5. **finding_limit** [deterministic] — The review contains at most eight findings.
6. **concrete_defect** [subjective] — Every finding describes a plausible runtime, security, data-integrity, or correctness failure rather than style or speculation.
7. **evidence_alignment** [subjective] — The cited line contains the operation responsible for the stated failure, and the rationale explains that connection.
8. **coverage** [subjective] — The review identifies distinct material defects visible in the supplied snippet, including interacting defects when present.
9. **precision** [subjective] — The review avoids unsupported assumptions, duplicates, and concerns outside the supplied code.

## Defects to look for

- Invalid structure, missing fields, out-of-range lines, duplicate findings, or more than eight findings.
- A correct defect attached to the wrong line.
- A rationale that names a generic risk without explaining the concrete failure path.
- A speculative finding that depends on an unstated framework, caller, or deployment assumption.
- A material defect omitted because the review stopped after finding an easier issue.
- A revision that fixes one issue while changing or regressing already-correct findings.

## Verification

The first five criteria are enforced by `agents/gates.py`. The final four are evaluated by the structured critic. The deterministic benchmark score remains the frozen category-and-line F1 in `evals/score.py` and is not replaced by critic satisfaction.
