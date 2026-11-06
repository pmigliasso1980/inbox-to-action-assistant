import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_architecture_audit_has_all_stages_and_no_new_spend():
    audit = json.loads((ROOT / "runs/architecture-audit.json").read_text())
    assert audit["new_api_cost_usd"] == 0
    assert audit["noise_floor"] > 0
    assert [row["stage"] for row in audit["rows"]] == [
        "Zero-shot baseline", "Reflection (M2)", "Tool use (M3)", "Planning (M4)",
        "Generator–critic (M5)", "Review panel (M5)", "Gated chain (M6)",
        "Routed (M6)", "Orchestrator (M6)",
    ]


def test_full_set_progression_has_no_promotable_lift_over_noise():
    audit = json.loads((ROOT / "runs/architecture-audit.json").read_text())
    values = audit["comparable_full_set_progression"]
    assert max(b - a for a, b in zip(values, values[1:])) <= audit["noise_floor"]
