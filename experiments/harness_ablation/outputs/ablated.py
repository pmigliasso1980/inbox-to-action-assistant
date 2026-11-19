"""Output after ablating executable verification from the harness."""


def build_followup(analysis: dict) -> dict:
    severity = analysis.get("severity")
    recurrence = analysis.get("recurrence_key")
    evidence = analysis.get("evidence", [])
    if severity == "SEV-1" and recurrence:
        action = "page_now"
    elif severity == "SEV-1" or recurrence:
        action = "schedule_review"
    else:
        action = "monitor"
    return {
        "action": action,
        "rationale": f"severity={severity}; recurrence={recurrence or 'none'}",
        "evidence_count": len(evidence),
    }
