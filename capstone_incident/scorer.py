"""Objective exact-match scoring for incident analyses."""
from __future__ import annotations

FIELDS = ("primary_cause", "severity", "remediation", "owner", "recurrence_key")


def score(expected: dict, actual: dict) -> dict:
    matches = {field: actual.get(field) == expected.get(field) for field in FIELDS}
    return {"score": sum(matches.values()) / len(FIELDS), "matches": matches,
            "missing": [field for field in FIELDS if field not in actual]}
