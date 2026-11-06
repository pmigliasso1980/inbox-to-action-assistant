"""Typed graph queries, including the three queries named in ADR-001."""
from __future__ import annotations

from pydantic import BaseModel

from graph.store import EdgeRecord, GraphStore, NodeRecord


class ClaimWithProvenance(BaseModel):
    claim: NodeRecord
    sources: list[NodeRecord]
    support_edges: list[EdgeRecord]


class ChangeRecord(BaseModel):
    claim_id: str
    statement: str
    run_id: str
    prompt_version: str


class DecisionTrace(BaseModel):
    claim: NodeRecord
    entities: list[NodeRecord]
    provenance: ClaimWithProvenance
    supersedes: list[str]


def current_claims_about(store: GraphStore, entity_id: str) -> list[NodeRecord]:
    current = {node.id: node for node in store.current_claims()}
    claim_ids = {edge.source_id for edge in store.edges(target_id=entity_id, edge_types={"mentions"})}
    return [current[claim_id] for claim_id in sorted(claim_ids & current.keys())]


def provenance_of(store: GraphStore, claim_id: str) -> ClaimWithProvenance:
    claim = store.get_node(claim_id)
    if claim is None or claim.node_type != "Claim":
        raise KeyError(claim_id)
    edges = store.provenance_edges(claim_id)
    sources = [store.get_node(edge.target_id) for edge in edges]
    return ClaimWithProvenance(claim=claim, sources=[x for x in sources if x is not None], support_edges=edges)


def contradictions(store: GraphStore) -> list[tuple[NodeRecord, NodeRecord]]:
    pairs = []
    for edge in store.edges(edge_types={"contradicts"}):
        left, right = store.get_node(edge.source_id), store.get_node(edge.target_id)
        if left and right:
            pairs.append((left, right))
    return pairs


def history_of(store: GraphStore, claim_id: str) -> list[NodeRecord]:
    node = store.get_node(claim_id)
    if node is None or node.node_type != "Claim":
        raise KeyError(claim_id)
    # Find the oldest reachable target, then follow incoming edges toward newest.
    oldest = node
    while True:
        outgoing = store.edges(source_id=oldest.id, edge_types={"supersedes"})
        if not outgoing:
            break
        oldest = store.get_node(outgoing[0].target_id)  # type: ignore[assignment]
        assert oldest
    history = [oldest]
    while True:
        incoming = store.edges(target_id=history[-1].id, edge_types={"supersedes"})
        if not incoming:
            break
        next_node = store.get_node(incoming[0].source_id)
        assert next_node
        history.append(next_node)
    return history


def changed_findings(store: GraphStore, entity_id: str) -> list[ChangeRecord]:
    claim_ids = {edge.source_id for edge in store.edges(target_id=entity_id, edge_types={"mentions"})}
    rows = []
    for claim_id in sorted(claim_ids):
        claim = store.get_node(claim_id)
        if claim is None:
            continue
        run = store.get_node(claim.properties["created_by_run"])
        rows.append(ChangeRecord(
            claim_id=claim.id, statement=claim.properties["statement"],
            run_id=run.id if run else "missing",
            prompt_version=run.properties["prompt_version"] if run else "missing",
        ))
    return rows


def decision_provenance(store: GraphStore, claim_id: str) -> DecisionTrace:
    claim = store.get_node(claim_id)
    if claim is None:
        raise KeyError(claim_id)
    mention_edges = store.edges(source_id=claim_id, edge_types={"mentions"})
    entities = [store.get_node(edge.target_id) for edge in mention_edges]
    return DecisionTrace(
        claim=claim,
        entities=[x for x in entities if x is not None],
        provenance=provenance_of(store, claim_id),
        supersedes=[edge.target_id for edge in store.edges(source_id=claim_id, edge_types={"supersedes"})],
    )


def rejected_assumptions(store: GraphStore, entity_id: str) -> list[NodeRecord]:
    return [
        claim for claim in current_claims_about(store, entity_id)
        if claim.properties.get("claim_kind") == "rejected_assumption"
    ]
