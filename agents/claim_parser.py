"""Deterministic claim parser used by the graph-grounded evaluation replay."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from graph.store import canonical_id

ROOT = Path(__file__).resolve().parents[1]
UNMAPPABLE_LOG = ROOT / "runs/unmappable-predicates.jsonl"
PREDICATES = {
    "has_defect": {"has_defect", "contains", "defect", "bug"},
    "labelled_category": {"labelled_category", "category", "classified_as"},
    "included_in_dataset": {"included_in_dataset", "dataset_member"},
    "supported_at_line": {"supported_at_line", "line", "located_at"},
}


class DraftClaim(BaseModel):
    claim_text: str
    subject: str
    predicate: str
    object: str | None
    location_in_draft: str
    subject_surface: str
    object_surface: str | None = None


class ParseResult(BaseModel):
    claims: list[DraftClaim]
    unparseable: list[str]
    factual_claim_count: int
    coverage: float


def normalize_predicate(raw: str, *, log_context: dict[str, Any] | None = None) -> str | None:
    value = raw.strip().lower().replace(" ", "_")
    for canonical, aliases in PREDICATES.items():
        if value in aliases:
            return canonical
    UNMAPPABLE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with UNMAPPABLE_LOG.open("a") as handle:
        handle.write(json.dumps({"predicate": raw, "context": log_context or {}}, sort_keys=True) + "\n")
    return None


def parse_review(file_name: str, draft: dict[str, Any]) -> ParseResult:
    """Triple-ify structured review defects; never collapse parse failures into unsupported."""
    claims: list[DraftClaim] = []
    unparseable: list[str] = []
    defects = draft.get("defects", [])
    for index, defect in enumerate(defects, 1):
        category = defect.get("category")
        description = defect.get("description") or defect.get("rationale")
        line = defect.get("line")
        if not category or not description or not isinstance(line, int):
            unparseable.append(f"defects[{index}]: missing category, description, or integer line")
            continue
        predicate = normalize_predicate("has_defect", log_context={"file": file_name, "index": index})
        if predicate is None:
            unparseable.append(description)
            continue
        claims.append(DraftClaim(
            claim_text=f"{file_name} contains {category} at line {line}: {description}",
            subject=canonical_id("file", file_name, {"language": "python"}),
            predicate=predicate,
            object=canonical_id("defect_category", category),
            location_in_draft=f"defects[{index}]",
            subject_surface=file_name,
            object_surface=category,
        ))
    total = len(defects)
    return ParseResult(
        claims=claims, unparseable=unparseable, factual_claim_count=total,
        coverage=(len(claims) / total if total else 1.0),
    )
