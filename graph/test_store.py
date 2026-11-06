from pathlib import Path

import pytest

from graph.queries import history_of
from graph.store import GraphStore, SourceRef, canonical_id, content_hash


def setup(store: GraphStore):
    store.write_node("Run", {"id": "run-1", "started_at": "2026-11-05T00:00:00Z", "model": "offline", "effort": "none", "prompt_version": "v1", "dataset_version": "1.1.0"})
    store.write_node("Source", {"id": "src-1", "kind": "code", "locator": "file.py", "content_hash": content_hash("x = 1")})
    entity = store.upsert_entity("file", "file.py")
    return entity


def claim(store: GraphStore, statement: str, entity: str, run: str = "run-1") -> str:
    return store.write_claim(statement, [SourceRef(source_id="src-1", span="x = 1")], 0.9, run, [entity])


def test_canonical_id_idempotence_and_alias_preservation():
    store = GraphStore()
    ids = [store.upsert_entity("company", value) for value in ["Acme Inc.", "ACME", " acme corporation "]]
    assert len(set(ids)) == 1
    assert store.get_node(ids[0]).properties["aliases"] == ["Acme Inc.", "ACME", " acme corporation "]
    assert canonical_id("file", "src/example.py") == canonical_id("file", "EXAMPLE.PY")


def test_provenance_less_claim_raises():
    store = GraphStore(); entity = setup(store)
    with pytest.raises(ValueError, match="claim_provenance"):
        store.write_claim("unsupported", [], 0.9, "run-1", [entity])
    with pytest.raises(ValueError, match="claim_write_path"):
        store.write_node("Claim", {"id": "bad", "statement": "x", "confidence": 1.0, "created_by_run": "run-1"})


def test_superseding_preserves_original_and_current_query():
    store = GraphStore(); entity = setup(store)
    old = claim(store, "old", entity)
    new = store.supersede_claim(old, "new", [SourceRef(source_id="src-1", span="x = 1")], 0.95, "run-1", [entity])
    assert store.get_node(old).properties["statement"] == "old"
    assert [x.id for x in store.current_claims()] == [new]


def test_three_deep_supersede_chain_resolves_one_current():
    store = GraphStore(); entity = setup(store)
    one = claim(store, "one", entity)
    two = store.supersede_claim(one, "two", [SourceRef(source_id="src-1", span="x = 1")], 0.9, "run-1", [entity])
    three = store.supersede_claim(two, "three", [SourceRef(source_id="src-1", span="x = 1")], 0.9, "run-1", [entity])
    assert [x.properties["statement"] for x in history_of(store, three)] == ["one", "two", "three"]
    assert [x.id for x in store.current_claims()] == [three]


def test_unknown_node_and_required_properties_enforced():
    store = GraphStore()
    with pytest.raises(ValueError, match="known_node_type"):
        store.write_node("Mystery", {"id": "x"})
    with pytest.raises(ValueError, match="required_property"):
        store.write_node("Source", {"id": "x", "kind": "code"})


def test_unknown_edge_and_legal_endpoints_enforced():
    store = GraphStore(); entity = setup(store)
    with pytest.raises(ValueError, match="known_edge_type"):
        store.write_edge("likes", entity, "src-1")
    with pytest.raises(ValueError, match="legal_edge_endpoints"):
        store.write_edge("supports", entity, "src-1")


def test_confidence_range_and_span_enforced():
    store = GraphStore(); entity = setup(store)
    with pytest.raises(ValueError, match="confidence_range"):
        store.write_claim("bad", [SourceRef(source_id="src-1", span="x = 1")], 1.2, "run-1", [entity])
    with pytest.raises(Exception):
        SourceRef(source_id="src-1", span="")


def test_supersedes_same_type_and_cycle_enforced():
    store = GraphStore(); entity = setup(store)
    first = claim(store, "first", entity)
    second = claim(store, "second", entity)
    with pytest.raises(ValueError, match="supersedes_same_type"):
        store.write_edge("supersedes", first, "src-1")
    store.write_edge("supersedes", second, first)
    with pytest.raises(ValueError, match="supersedes_acyclic"):
        store.write_edge("supersedes", first, second)


def test_claim_edges_and_typed_queries():
    store = GraphStore(); entity = setup(store)
    claim_id = claim(store, "supported", entity)
    assert store.provenance_edges(claim_id)[0].properties["span"] == "x = 1"
