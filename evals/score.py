"""Deterministic precision/recall/F1 scoring for seeded code defects."""
from __future__ import annotations

import json


def score_item(expected: dict, output: str) -> dict:
    try:
        parsed = json.loads(output)
        predicted = parsed.get("defects", [])
    except (json.JSONDecodeError, AttributeError):
        predicted = []
    gold = {(d["category"], int(d["line"])) for d in expected.get("defects", [])}
    got = {(d.get("category"), int(d.get("line", -1))) for d in predicted if isinstance(d, dict)}
    true_positive = len(gold & got)
    precision = true_positive / len(got) if got else (1.0 if not gold else 0.0)
    recall = true_positive / len(gold) if gold else (1.0 if not got else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"score": f1, "detail": {"precision": precision, "recall": recall,
            "true_positive": true_positive, "predicted": len(got), "expected": len(gold),
            "missed": sorted(gold - got), "extra": sorted(got - gold)}}
