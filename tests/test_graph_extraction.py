import json
from pathlib import Path

from agents.extractor import SourceDocument, extract
from graph.audit import audit_store
from graph.extraction_pipeline import load_ground_truth, run
from graph.store import GraphStore, content_hash


def test_ground_truth_predeclares_ten_documents():
    rows = load_ground_truth()
    assert len(rows) == 10
    assert all(row["entities"] and row["claims"] for row in rows)


def test_extractor_outputs_structured_triples_and_verbatim_spans():
    row = load_ground_truth()[0]
    result = extract(SourceDocument(document_id=row["document_id"], file=row["file"], content=row["content"]))
    assert result.claims[0].predicate == "has_defect"
    assert result.claims[0].source_span in row["content"]


def test_pipeline_measures_nontrivial_quality_without_api_calls(tmp_path):
    result = run(tmp_path / "extraction.db")
    assert result["new_api_cost_usd"] == 0
    assert result["entity_quality"]["precision"] < 1
    assert result["claim_quality"]["precision"] == 0.9
    assert result["claim_quality"]["span_passed_but_unsupported"] == 1
    assert result["contradictions_written"] == 1
    assert not result["audit"]["claims_with_no_provenance"]


def test_audit_detects_stale_source_content():
    store = GraphStore()
    store.write_node("Source", {"id": "s", "kind": "text", "locator": "x", "content_hash": content_hash("old"), "content": "new"})
    assert audit_store(store)["stale_source_hashes"] == ["s"]
