"""Schema-constrained deterministic extractor for the frozen code corpus."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    document_id: str
    file: str
    content: str


class ExtractedEntity(BaseModel):
    surface_form: str
    entity_type: str
    normalized_name: str


class ExtractedClaim(BaseModel):
    statement: str
    subject_surface: str
    predicate: str
    object_surface: str | None
    source_span: str
    confidence: float = Field(ge=0, le=1)


class Extraction(BaseModel):
    entities: list[ExtractedEntity]
    claims: list[ExtractedClaim]


RULES = [
    ("range(n + 1)", "off_by_one", 0.95),
    ("tags=[]", "mutable_default", 0.92),
    ("except Exception:", "swallowed_exception", 0.62),
    ("SELECT * FROM users", "sql_injection", 0.88),
    ("Path(root) / filename", "path_traversal", 0.82),
    ("client.post('/notify'", "missing_await", 0.78),
    ("/ len(values)", "division_by_zero", 0.76),
    ("user.profile.name.strip()", "null_dereference", 0.72),
    # resource_leak deliberately absent so recall is measured honestly.
    ("random.randint(0, 9)", "insecure_random", 0.55),
]


def normalize_name(value: str) -> str:
    return " ".join("".join(char.lower() if char.isalnum() else " " for char in value).split())


def extract(document: SourceDocument) -> Extraction:
    entities = [ExtractedEntity(surface_form=document.file, entity_type="file", normalized_name=normalize_name(document.file))]
    claims = []
    for number, line in enumerate(document.content.splitlines(), 1):
        for needle, category, confidence in RULES:
            if needle in line:
                entities.append(ExtractedEntity(surface_form=category, entity_type="defect_category", normalized_name=normalize_name(category)))
                claims.append(ExtractedClaim(
                    statement=f"{document.file} contains {category} at line {number}.",
                    subject_surface=document.file, predicate="has_defect", object_surface=category,
                    source_span=line, confidence=confidence,
                ))
    if document.document_id == "item-003":
        # Deliberate plausible-but-wrong extraction: span exists but does not support the claim.
        entities.extend([
            ExtractedEntity(surface_form="configs.py", entity_type="file", normalized_name="configs py"),
            ExtractedEntity(surface_form="path_traversal", entity_type="defect_category", normalized_name="path traversal"),
        ])
        span = document.content.splitlines()[0]
        claims.append(ExtractedClaim(
            statement="config.py contains path_traversal at line 1.", subject_surface=document.file,
            predicate="has_defect", object_surface="path_traversal", source_span=span, confidence=0.65,
        ))
    return Extraction(entities=entities, claims=claims)
