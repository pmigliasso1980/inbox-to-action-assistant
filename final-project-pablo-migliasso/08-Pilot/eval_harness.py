#!/usr/bin/env python3
"""Deterministic structural checks for the synthetic referral golden set."""

import json
from collections import Counter
from pathlib import Path

REQUIRED_FIELDS = {
    "patient_name", "dob", "referring_provider", "specialty", "urgency", "needs_human_review"
}


def main() -> None:
    path = Path(__file__).with_name("golden-set.jsonl")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert len(rows) >= 15, "Golden set must contain at least 15 cases"
    assert len({row["id"] for row in rows}) == len(rows), "Case IDs must be unique"
    categories = Counter(row["category"] for row in rows)
    for required in ("typical", "exception", "known_failure", "adversarial"):
        assert categories[required] >= 3, f"Need at least three {required} cases"
    for row in rows:
        assert set(row["expected"]) == REQUIRED_FIELDS, f"Unexpected schema in {row['id']}"
        expected = row["expected"]
        missing = any(expected[field] is None for field in REQUIRED_FIELDS - {"needs_human_review"})
        if missing:
            assert expected["needs_human_review"], f"Missing data must route {row['id']} to review"
        if row["category"] in {"exception", "known_failure", "adversarial"}:
            assert expected["needs_human_review"], f"Risk case {row['id']} must require review"
    print(f"PASS: {len(rows)} synthetic cases")
    print("Categories:", dict(sorted(categories.items())))
    print("PASS: schema, uniqueness, coverage, and human-review safety invariants")


if __name__ == "__main__":
    main()
