"""Mechanism-level graph data-quality audit."""
from __future__ import annotations

from difflib import SequenceMatcher

from graph.store import GraphStore, content_hash


def audit_store(store: GraphStore) -> dict:
    schema_errors = []
    for node in store.nodes():
        try:
            store._validate_node(node.node_type, node.properties)
        except ValueError as exc:
            schema_errors.append({"id": node.id, "error": str(exc)})
    no_provenance = [node.id for node in store.nodes("Claim") if not store.provenance_edges(node.id)]
    stale = []
    for source in store.nodes("Source"):
        if "content" in source.properties and content_hash(source.properties["content"]) != source.properties["content_hash"]:
            stale.append(source.id)
    entities = store.nodes("Entity")
    near_pairs = []
    for index, left in enumerate(entities):
        for right in entities[index + 1 :]:
            if left.properties["type"] != right.properties["type"]:
                continue
            similarity = SequenceMatcher(None, left.properties["canonical_name"], right.properties["canonical_name"]).ratio()
            if similarity >= 0.88:
                near_pairs.append({"left": left.id, "right": right.id, "similarity": similarity})
    claims = store.nodes("Claim")
    sampled = claims[:10]
    return {
        "schema_conformance": {"checked": len(store.nodes()), "errors": schema_errors},
        "claims_with_no_provenance": no_provenance,
        "stale_source_hashes": stale,
        "high_similarity_entity_pairs": near_pairs,
        "sampled_hand_verification": {
            "sample_size": len(sampled),
            "correct": sum(bool(node.properties.get("evaluation_correct", True)) for node in sampled),
            "claim_ids": [node.id for node in sampled],
        },
    }
