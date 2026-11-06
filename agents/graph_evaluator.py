"""Three-way graph verification with provenance weighting and staleness checks."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from agents.claim_parser import DraftClaim
from graph.queries import current_claims_about, provenance_of
from graph.store import GraphStore, canonical_id, content_hash

Verdict = Literal["supported", "unsupported", "contradicted", "unparseable"]
Action = Literal["correct", "remove", "investigate", "cite"]


class GroundedFinding(BaseModel):
    claim: DraftClaim | None
    verdict: Verdict
    graph_evidence: list[str]
    conflicting_statement: str | None
    source_locator: str | None
    source_span: str | None
    recommended_action: Action
    deciding_claim_id: str | None
    confidence: float | None
    evidence_quality: str
    stale: bool


def _object_id(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text.startswith("ent_") else canonical_id("defect_category", text)


def _source_details(store: GraphStore, claim_id: str) -> tuple[str | None, str | None, bool, str]:
    prov = provenance_of(store, claim_id)
    if not prov.sources:
        return None, None, False, "none"
    source = prov.sources[0]
    edge = prov.support_edges[0]
    props = source.properties
    span = edge.properties.get("span")
    stale = bool("content" in props and content_hash(props["content"]) != props["content_hash"])
    kind = props.get("kind", "unknown")
    quality = "primary_document_with_span" if span and kind in {"python", "primary_document"} else "model_extraction"
    return props.get("locator"), span, stale, quality


def verify(claim: DraftClaim, store: GraphStore, *, confidence_threshold: float = 0.7) -> GroundedFinding:
    candidates = [
        node for node in current_claims_about(store, claim.subject)
        if node.properties.get("predicate") == claim.predicate
    ]
    matching = [node for node in candidates if _object_id(node.properties.get("object")) == claim.object]
    deciding = matching[0] if matching else (max(candidates, key=lambda n: n.properties["confidence"]) if candidates else None)
    if deciding is None:
        return GroundedFinding(
            claim=claim, verdict="unsupported", graph_evidence=[], conflicting_statement=None,
            source_locator=None, source_span=None, recommended_action="investigate",
            deciding_claim_id=None, confidence=None, evidence_quality="none", stale=False,
        )
    locator, span, stale, quality = _source_details(store, deciding.id)
    confidence = float(deciding.properties["confidence"])
    high_quality = quality in {"test_result", "api_response", "primary_document_with_span"}
    weighted = high_quality and confidence >= confidence_threshold and not stale
    verdict: Verdict = "supported" if matching else "contradicted"
    action: Action = ("cite" if verdict == "supported" else "remove") if weighted else "investigate"
    return GroundedFinding(
        claim=claim, verdict=verdict,
        graph_evidence=[node.properties["statement"] for node in candidates],
        conflicting_statement=None if matching else deciding.properties["statement"],
        source_locator=locator, source_span=span, recommended_action=action,
        deciding_claim_id=deciding.id, confidence=confidence,
        evidence_quality=quality, stale=stale,
    )


def unparseable_finding(message: str) -> GroundedFinding:
    return GroundedFinding(
        claim=None, verdict="unparseable", graph_evidence=[], conflicting_statement=message,
        source_locator=None, source_span=None, recommended_action="investigate",
        deciding_claim_id=None, confidence=None, evidence_quality="none", stale=False,
    )
