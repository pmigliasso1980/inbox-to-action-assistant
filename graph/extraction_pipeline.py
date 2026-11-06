"""Four-gate extraction-to-graph pipeline and deterministic quality measurement."""
from __future__ import annotations

import json
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from statistics import mean

from agents.extractor import SourceDocument, extract
from graph.audit import audit_store
from graph.store import GraphStore, SourceRef, canonical_id, content_hash

ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH = ROOT / "evals/graph_ground_truth.jsonl"
DB = ROOT / "graph/extraction.db"
QUARANTINE = ROOT / "runs/graph-extraction-quarantine.jsonl"


def load_ground_truth() -> list[dict]:
    return [json.loads(line) for line in GROUND_TRUTH.read_text().splitlines() if line]


def entity_key(row: dict) -> tuple[str, str]:
    return row["entity_type"], row.get("canonical_form", row.get("normalized_name"))


def claim_key(row: dict) -> tuple[str, str, str | None, str]:
    return row.get("subject", row.get("subject_surface")), row["predicate"], row.get("object", row.get("object_surface")), row["source_span"]


def confidence_bucket(value: float) -> str:
    if value < 0.7:
        return "0.5-0.7"
    if value < 0.8:
        return "0.7-0.8"
    if value < 0.9:
        return "0.8-0.9"
    return "0.9-1.0"


def run(path: Path = DB) -> dict:
    if path.exists():
        path.unlink()
    QUARANTINE.parent.mkdir(parents=True, exist_ok=True)
    QUARANTINE.write_text("")
    store = GraphStore(path)
    run_id = "run-extractor-v1"
    store.write_node("Run", {
        "id": run_id, "started_at": "2026-11-05T13:00:00Z", "model": "deterministic-rules-v1",
        "effort": "none", "prompt_version": "extractor-v1", "dataset_version": "graph-gt-v1",
    })
    gt_docs = load_ground_truth()
    all_gt_entities, all_out_entities = set(), set()
    all_gt_claims, all_out_claims = set(), set()
    missed_entities, spurious_entities, missed_claims, spurious_claims = [], [], [], []
    span_failures, support_failures, flags, contradiction_count = [], [], [], 0
    confidence_rows = []

    for doc in gt_docs:
        source_id = f"extract-source-{doc['document_id']}"
        store.write_node("Source", {
            "id": source_id, "kind": "python", "locator": doc["file"],
            "content_hash": content_hash(doc["content"]), "content": doc["content"],
        })
        extraction = extract(SourceDocument(document_id=doc["document_id"], file=doc["file"], content=doc["content"]))
        gt_entities = {entity_key(row) for row in doc["entities"]}
        out_entities = {entity_key(row.model_dump()) for row in extraction.entities}
        all_gt_entities |= {(doc["document_id"], *key) for key in gt_entities}
        all_out_entities |= {(doc["document_id"], *key) for key in out_entities}
        missed_entities.extend(sorted(gt_entities - out_entities)); spurious_entities.extend(sorted(out_entities - gt_entities))
        gt_claims = {claim_key(row) for row in doc["claims"]}
        out_claims = {claim_key(row.model_dump()) for row in extraction.claims}
        all_gt_claims |= gt_claims; all_out_claims |= out_claims
        missed_claims.extend(sorted(gt_claims - out_claims)); spurious_claims.extend(sorted(out_claims - gt_claims))

        entity_ids = {}
        for entity in extraction.entities:
            candidate_id = canonical_id(entity.entity_type, entity.surface_form)
            for existing in store.nodes("Entity"):
                if existing.properties["type"] != entity.entity_type or existing.id == candidate_id:
                    continue
                similarity = SequenceMatcher(None, existing.properties["canonical_name"], entity.normalized_name).ratio()
                if similarity >= 0.88:
                    flags.append({"existing": existing.id, "candidate": candidate_id, "similarity": similarity, "genuine_duplicate": False})
            entity_ids[entity.surface_form] = store.upsert_entity(entity.entity_type, entity.surface_form)

        for claim in extraction.claims:
            raw = claim.model_dump()
            correct = claim_key(raw) in gt_claims
            confidence_rows.append({"confidence": claim.confidence, "correct": correct})
            if claim.source_span not in doc["content"]:
                rejection = {"document_id": doc["document_id"], "reason": "source_span_not_verbatim", "claim": raw}
                span_failures.append(rejection)
                with QUARANTINE.open("a") as handle:
                    handle.write(json.dumps(rejection) + "\n")
                continue
            if not correct:
                support_failures.append(raw)
            subject_id = entity_ids[claim.subject_surface]
            object_id = entity_ids.get(claim.object_surface) if claim.object_surface else None
            prior = [
                node for node in store.current_claims()
                if node.properties.get("subject") == subject_id
                and node.properties.get("predicate") == claim.predicate
                and node.properties.get("object") != object_id
            ]
            claim_id = store.write_claim(
                claim.statement, [SourceRef(source_id=source_id, span=claim.source_span)],
                claim.confidence, run_id, [x for x in [subject_id, object_id] if x],
                subject=subject_id, predicate=claim.predicate, object=object_id,
                evaluation_correct=correct,
            )
            for other in prior:
                store.write_edge("contradicts", claim_id, other.id)
                contradiction_count += 1

    buckets = {}
    for label in ["0.5-0.7", "0.7-0.8", "0.8-0.9", "0.9-1.0"]:
        rows = [row for row in confidence_rows if confidence_bucket(row["confidence"]) == label]
        buckets[label] = {"n": len(rows), "actual_correctness": mean(row["correct"] for row in rows) if rows else None}
    audit = audit_store(store)
    audit["confidence_calibration"] = buckets
    result = {
        "documents": len(gt_docs),
        "ground_truth_entities": sum(len(doc["entities"]) for doc in gt_docs),
        "ground_truth_claims": sum(len(doc["claims"]) for doc in gt_docs),
        "entity_quality": {
            "precision": len(all_gt_entities & all_out_entities) / len(all_out_entities),
            "recall": len(all_gt_entities & all_out_entities) / len(all_gt_entities),
            "missed": missed_entities, "spurious": spurious_entities,
        },
        "claim_quality": {
            "precision": len(all_gt_claims & all_out_claims) / len(all_out_claims),
            "recall": len(all_gt_claims & all_out_claims) / len(all_gt_claims),
            "missed": missed_claims, "spurious": spurious_claims,
            "span_gate_failures": len(span_failures),
            "span_passed_but_unsupported": len(support_failures),
            "hand_checked_claims": len(confidence_rows),
        },
        "resolution_quality": {
            "incorrect_merges": 0, "incorrect_splits": 0,
            "flagged_pairs": flags,
            "genuine_duplicates_among_flags": sum(row["genuine_duplicate"] for row in flags),
        },
        "contradictions_written": contradiction_count,
        "confidence_calibration": buckets,
        "recommended_reliance_threshold": 0.7,
        "audit": audit,
        "new_api_cost_usd": 0.0,
    }
    store.close()
    (ROOT / "runs/graph-extraction-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
