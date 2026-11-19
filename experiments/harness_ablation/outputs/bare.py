"""Output from the bare-context run."""


def build_followup(analysis: dict) -> dict:
    severity = analysis.get("severity")
    recurrence = analysis.get("recurrence_key")
    if severity == "SEV-1":
        action = "page_now"
    elif recurrence:
        action = "schedule_review"
    else:
        action = "monitor"
    return {
        "action": action,
        "rationale": f"severity={severity}, recurrence={recurrence}",
        "evidence_count": len(analysis.get("evidence", [])),
    }
