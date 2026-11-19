"""Output from the full-harness run."""

VALID_SEVERITIES = frozenset({"SEV-1", "SEV-2", "SEV-3"})


def build_followup(analysis: dict) -> dict:
    severity = analysis.get("severity")
    recurrence_raw = analysis.get("recurrence_key")
    evidence = analysis.get("evidence")
    if severity not in VALID_SEVERITIES:
        raise ValueError("severity must be SEV-1, SEV-2, or SEV-3")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence must be a nonempty list")
    if any(not isinstance(item, str) or not item.strip() for item in evidence):
        raise ValueError("every evidence item must be a nonblank string")
    if recurrence_raw is not None and not isinstance(recurrence_raw, str):
        raise ValueError("recurrence_key must be a string or null")
    recurrence = recurrence_raw.strip() if isinstance(recurrence_raw, str) else ""
    if severity == "SEV-1" and recurrence:
        action = "page_now"
    elif severity == "SEV-1" or recurrence:
        action = "schedule_review"
    else:
        action = "monitor"
    recurrence_label = recurrence or "none"
    return {
        "action": action,
        "rationale": f"severity={severity}; recurrence={recurrence_label}",
        "evidence_count": len(evidence),
    }
