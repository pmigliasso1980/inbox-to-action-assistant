from pathlib import Path

import pytest

from agents.claim_parser import parse_review
from agents.graph_evaluator import verify
from agents.graph_roles import ROLES, ScopedGraph
from graph.seed import seed
from graph.store import GraphStore


def test_parser_reports_coverage_and_canonicalizes():
    result = parse_review("src/range_total.py", {"defects": [{
        "category": "off_by_one", "line": 3, "rationale": "inclusive range"
    }, {"category": "missing-line"}]})
    assert result.coverage == .5
    assert len(result.unparseable) == 1
    assert result.claims[0].subject.startswith("ent_")


def test_three_way_verification(tmp_path: Path):
    path = tmp_path / "graph.db"
    seed(path)
    store = GraphStore(path)
    supported = parse_review("range_total.py", {"defects": [{
        "category": "off_by_one", "line": 3, "rationale": "inclusive range"
    }]}).claims[0]
    contradicted = supported.model_copy(update={
        "object": parse_review("range_total.py", {"defects": [{
            "category": "wrong_category", "line": 3, "rationale": "wrong"
        }]}).claims[0].object
    })
    missing = supported.model_copy(update={"subject": "ent_missing"})
    assert verify(supported, store).verdict == "supported"
    assert verify(contradicted, store).verdict == "contradicted"
    assert verify(missing, store).verdict == "unsupported"
    store.close()


@pytest.mark.parametrize("role", sorted(ROLES))
def test_each_role_rejects_forbidden_claim_write(tmp_path: Path, role: str):
    path = tmp_path / f"{role}.db"
    seed(path)
    access = ScopedGraph(GraphStore(path), role)
    if role == "tech_lead":
        with pytest.raises(PermissionError):
            access.write_artifact({}, "source-001")
    else:
        with pytest.raises(PermissionError):
            access.write_claim(statement="x", sources=[], confidence=.5, run_id="run-seed-v1", mentions=[])
    assert access.events[-1]["kind"] == "scope_violation"
    access.store.close()
