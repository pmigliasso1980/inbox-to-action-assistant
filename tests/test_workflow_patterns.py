import json
from pathlib import Path

from agents.orchestrator_patterns import SEED, hierarchical, orchestrate, plan_workers, shared_store
from agents.workflow_patterns import gate_candidates, normalize, replay_candidates, route_item, run_chain_item


ROOT = Path(__file__).resolve().parents[1]
ITEMS = [json.loads(line) for line in (ROOT / "evals/dataset.jsonl").read_text().splitlines() if line]


def test_semantic_and_reference_gate_catches_seeded_fault():
    item = ITEMS[3]
    verdict = gate_candidates(normalize(item), replay_candidates(item))
    assert not verdict.passed
    assert verdict.fallback == "escalate_expert"
    assert any("line 99" in error for error in verdict.violations)


def test_gated_chain_rescues_confident_wrong_output():
    item = ITEMS[3]
    ungated = run_chain_item(item, gated=False)
    gated = run_chain_item(item, gated=True)
    assert ungated["confident_wrong"]
    assert gated["rescued"]
    assert gated["score"] == 1.0


def test_router_includes_other_route_for_below_threshold():
    decision = route_item(ITEMS[6])
    assert decision.route == "other"
    assert decision.confidence < 0.85


def test_transcript_bottleneck_is_silent_but_artifacts_survive():
    transcript = orchestrate(20, "transcript")
    artifact = orchestrate(20, "artifact")
    assert transcript["compaction_triggered"] and not transcript["seed_survived"]
    assert transcript["context_errors"] == 0
    assert artifact["seed_survived"]


def test_hierarchy_and_shared_store_preserve_seed(tmp_path):
    assert hierarchical(20)["seed_survived"]
    result = shared_store(20, tmp_path / "findings.jsonl")
    assert result["seed_survived"]
    assert SEED in (tmp_path / "findings.jsonl").read_text()


def test_orchestrator_dynamically_expands_team_for_complex_security_item():
    roles = plan_workers(ITEMS[16])
    assert roles == ["correctness", "security", "robustness", "interaction-analysis"]
