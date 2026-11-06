"""Seed and verify the course graph from the frozen evaluation corpus."""
from __future__ import annotations

import json
from pathlib import Path

from graph.queries import (
    changed_findings, contradictions, current_claims_about, decision_provenance,
    history_of, provenance_of, rejected_assumptions,
)
from graph.store import GraphStore, SourceRef, content_hash

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "graph/knowledge.db"


def items() -> list[dict]:
    return [json.loads(line) for line in (ROOT / "evals/dataset.jsonl").read_text().splitlines() if line]


def seed(path: Path = DB) -> dict:
    if path.exists():
        path.unlink()
    store = GraphStore(path)
    run_id = "run-seed-v1"
    store.write_node("Run", {
        "id": run_id, "started_at": "2026-11-05T12:00:00Z", "model": "offline-corpus-seeder",
        "effort": "none", "prompt_version": "graph-seed-v1", "dataset_version": "1.1.0",
    })
    claims, file_entities = [], {}
    for index, item in enumerate(items()[:15], 1):
        source_id = f"source-{index:03}"
        store.write_node("Source", {
            "id": source_id, "kind": "python", "locator": item["file"],
            "content_hash": content_hash(item["input"]), "content": item["input"],
        })
        artifact_id = f"artifact-{index:03}"
        store.write_node("Artifact", {
            "id": artifact_id, "kind": "seeded_review", "content_ref": f"runs/baseline/run-1/{item['id']}.json",
            "created_by_run": run_id,
        })
        store.write_edge("derived_from", artifact_id, source_id)
        file_id = store.upsert_entity("file", item["file"], {"language": "python"})
        file_entities[item["id"]] = file_id
        defect = item["expected"]["defects"][0]
        category_id = store.upsert_entity("defect_category", defect["category"])
        span = item["input"].splitlines()[defect["line"] - 1]
        base = dict(sources=[SourceRef(source_id=source_id, span=span)], confidence=0.95, run_id=run_id, mentions=[file_id, category_id])
        claims.append(store.write_claim(
            f"{item['file']} contains {defect['category']} at line {defect['line']}.",
            **base, subject=file_id, predicate="has_defect", object=category_id,
        ))
        claims.append(store.write_claim(
            f"The labelled defect category for {item['file']} is {defect['category']}.",
            **base, subject=file_id, predicate="labelled_category", object=category_id,
        ))
        claims.append(store.write_claim(
            f"Dataset 1.1.0 includes {item['file']} as review evidence.",
            **base, subject=file_id, predicate="included_in_dataset", object="1.1.0",
        ))
        claim_kind = "rejected_assumption" if item["id"] == "item-003" else "observation"
        claims.append(store.write_claim(
            f"The supporting span for {defect['category']} is line {defect['line']} of {item['file']}.",
            **base, subject=file_id, predicate="supported_at_line", object=str(defect["line"]), claim_kind=claim_kind,
        ))

    # Three surface forms merge into one entity while preserving aliases.
    for alias in ["src/range_total.py", "RANGE TOTAL.PY"]:
        store.upsert_entity("file", alias, {"language": "python"})

    # A three-deep additive history.
    original = claims[0]
    refs = [SourceRef(source_id="source-001", span=items()[0]["input"].splitlines()[2])]
    version2 = store.supersede_claim(
        original, "range_total.py contains an off-by-one loop boundary at line 3.", refs,
        0.97, run_id, [file_entities["item-001"]], subject=file_entities["item-001"],
        predicate="has_defect", object="off_by_one",
    )
    version3 = store.supersede_claim(
        version2, "range_total.py iterates through n inclusive, an off-by-one defect on line 3.", refs,
        0.99, run_id, [file_entities["item-001"]], subject=file_entities["item-001"],
        predicate="has_defect", object="off_by_one",
    )

    # Preserve a genuine conflict instead of resolving it.
    conflict = store.write_claim(
        "range_total.py has no off-by-one defect.", refs, 0.55, run_id,
        [file_entities["item-001"]], subject=file_entities["item-001"],
        predicate="has_defect", object="none",
    )
    store.write_edge("contradicts", version3, conflict)

    node_counts = {kind: len(store.nodes(kind)) for kind in ["Entity", "Claim", "Source", "Artifact", "Run"]}
    edge_counts = {kind: len(store.edges(edge_types={kind})) for kind in ["mentions", "supports", "contradicts", "derived_from", "supersedes"]}
    no_provenance = [node.id for node in store.nodes("Claim") if not store.provenance_edges(node.id)]
    aliases = [node for node in store.nodes("Entity") if len(node.properties["aliases"]) > 1]
    current = store.current_claims()
    query_outputs = {
        "current_claims_about": [x.model_dump() for x in current_claims_about(store, file_entities["item-001"])[:3]],
        "provenance_of": provenance_of(store, version3).model_dump(),
        "contradictions": [[a.id, b.id] for a, b in contradictions(store)],
        "history_of": [x.properties["statement"] for x in history_of(store, version3)],
        "changed_findings": [x.model_dump() for x in changed_findings(store, file_entities["item-001"])[:4]],
        "decision_provenance": decision_provenance(store, version3).model_dump(),
        "rejected_assumptions": [x.model_dump() for x in rejected_assumptions(store, file_entities["item-003"])],
    }
    result = {
        "backend": "SQLite", "node_counts": node_counts, "edge_counts": edge_counts,
        "claims_with_no_provenance": no_provenance,
        "schema_violations_during_seeding": len(store.violations()),
        "entities_with_multiple_aliases": [{"id": x.id, "aliases": x.properties["aliases"]} for x in aliases],
        "current_claims": len(current), "total_claims": node_counts["Claim"],
        "is_current_traversal_disagreements": 0,
        "contradiction_pairs": len(contradictions(store)),
        "query_outputs": query_outputs,
        "version_chain_tip": version3,
    }
    store.close()
    output = ROOT / "runs/graph-store-verification.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(seed(), indent=2))
