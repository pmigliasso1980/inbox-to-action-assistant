"""Minimal typed graph store with provenance and additive-write enforcement."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


NODE_SCHEMA: dict[str, dict[str, type]] = {
    "Entity": {"id": str, "type": str, "canonical_name": str, "aliases": list},
    "Claim": {"id": str, "statement": str, "confidence": float, "created_by_run": str},
    "Source": {"id": str, "kind": str, "locator": str, "content_hash": str},
    "Artifact": {"id": str, "kind": str, "content_ref": str, "created_by_run": str},
    "Run": {"id": str, "started_at": str, "model": str, "effort": str, "prompt_version": str, "dataset_version": str},
}

EDGE_ENDPOINTS: dict[str, set[tuple[str, str]]] = {
    "mentions": {("Claim", "Entity")},
    "supports": {("Claim", "Source")},
    "contradicts": {("Claim", "Claim")},
    "derived_from": {("Claim", "Source"), ("Artifact", "Source")},
    "supersedes": {("Claim", "Claim"), ("Artifact", "Artifact")},
}


class SourceRef(BaseModel):
    source_id: str
    span: str = Field(min_length=1)


class NodeRecord(BaseModel):
    id: str
    node_type: Literal["Entity", "Claim", "Source", "Artifact", "Run"]
    properties: dict[str, Any]


class EdgeRecord(BaseModel):
    id: int
    edge_type: Literal["mentions", "supports", "contradicts", "derived_from", "supersedes"]
    source_id: str
    target_id: str
    properties: dict[str, Any]


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _normalize(raw_name: str) -> str:
    value = raw_name.strip().lower().replace("\\", "/")
    value = re.sub(r"^(?:\./|src/|lib/|app/)+", "", value)
    value = re.sub(r"^(?:ticket|issue|bug)[-:#\s]+", "", value)
    value = re.sub(r"\b(?:incorporated|inc|limited|ltd|corporation|corp|llc)\b\.?", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def canonical_id(entity_type: str, raw_name: str, attrs: dict | None = None) -> str:
    """Return a deterministic id after domain-noise normalization."""
    attrs = attrs or {}
    identity_attrs = {key: attrs[key] for key in sorted(attrs) if key in {"namespace", "language"}}
    payload = json.dumps([entity_type.lower(), _normalize(raw_name), identity_attrs], sort_keys=True)
    return f"ent_{hashlib.sha256(payload.encode()).hexdigest()[:20]}"


class GraphStore:
    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS nodes(
              id TEXT PRIMARY KEY, node_type TEXT NOT NULL, properties TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS edges(
              id INTEGER PRIMARY KEY AUTOINCREMENT, edge_type TEXT NOT NULL,
              source_id TEXT NOT NULL REFERENCES nodes(id),
              target_id TEXT NOT NULL REFERENCES nodes(id), properties TEXT NOT NULL,
              UNIQUE(edge_type, source_id, target_id, properties)
            );
            CREATE TABLE IF NOT EXISTS violations(
              id INTEGER PRIMARY KEY AUTOINCREMENT, rule TEXT NOT NULL,
              detail TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """
        )

    def close(self) -> None:
        self.db.close()

    def _violate(self, rule: str, detail: str) -> None:
        self.db.execute(
            "INSERT INTO violations(rule,detail,created_at) VALUES(?,?,?)",
            (rule, detail, datetime.now(timezone.utc).isoformat()),
        )
        self.db.commit()
        raise ValueError(f"{rule}: {detail}")

    def _validate_node(self, node_type: str, props: dict) -> None:
        if node_type not in NODE_SCHEMA:
            self._violate("known_node_type", f"unknown node type {node_type!r}")
        for name, expected in NODE_SCHEMA[node_type].items():
            if name not in props:
                self._violate("required_property", f"{node_type}.{name} is required")
            if not isinstance(props[name], expected):
                self._violate("property_type", f"{node_type}.{name} must be {expected.__name__}")
        if node_type == "Claim" and not 0 <= props["confidence"] <= 1:
            self._violate("confidence_range", "Claim.confidence must be in [0, 1]")

    def write_node(self, node_type: str, props: dict) -> str:
        if node_type == "Claim":
            self._violate("claim_write_path", "Claims must be created through write_claim")
        self._validate_node(node_type, props)
        self.db.execute(
            "INSERT INTO nodes(id,node_type,properties) VALUES(?,?,?)",
            (props["id"], node_type, json.dumps(props, sort_keys=True)),
        )
        self.db.commit()
        return props["id"]

    def upsert_entity(self, entity_type: str, surface_form: str, attrs: dict | None = None) -> str:
        entity_id = canonical_id(entity_type, surface_form, attrs)
        existing = self.get_node(entity_id)
        if existing:
            aliases = list(existing.properties["aliases"])
            if surface_form not in aliases:
                aliases.append(surface_form)
                props = existing.properties | {"aliases": aliases}
                self.db.execute("UPDATE nodes SET properties=? WHERE id=?", (json.dumps(props, sort_keys=True), entity_id))
                self.db.commit()
            return entity_id
        props = {
            "id": entity_id, "type": entity_type,
            "canonical_name": _normalize(surface_form), "aliases": [surface_form],
        }
        return self.write_node("Entity", props)

    def get_node(self, node_id: str) -> NodeRecord | None:
        row = self.db.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
        return None if row is None else NodeRecord(id=row["id"], node_type=row["node_type"], properties=json.loads(row["properties"]))

    def write_edge(self, edge_type: str, source_id: str, target_id: str, properties: dict | None = None) -> int:
        properties = properties or {}
        if edge_type not in EDGE_ENDPOINTS:
            self._violate("known_edge_type", f"unknown edge type {edge_type!r}")
        source, target = self.get_node(source_id), self.get_node(target_id)
        if source is None or target is None:
            self._violate("edge_endpoint_exists", f"missing endpoint for {source_id}->{target_id}")
        assert source and target
        if edge_type == "supersedes" and source.node_type != target.node_type:
            self._violate("supersedes_same_type", "supersedes endpoints must have the same type")
        if (source.node_type, target.node_type) not in EDGE_ENDPOINTS[edge_type]:
            self._violate("legal_edge_endpoints", f"{edge_type} cannot connect {source.node_type}->{target.node_type}")
        if edge_type == "supersedes":
            if source_id == target_id or self._reachable(target_id, source_id, "supersedes"):
                self._violate("supersedes_acyclic", f"edge {source_id}->{target_id} creates a cycle")
        cursor = self.db.execute(
            "INSERT OR IGNORE INTO edges(edge_type,source_id,target_id,properties) VALUES(?,?,?,?)",
            (edge_type, source_id, target_id, json.dumps(properties, sort_keys=True)),
        )
        self.db.commit()
        row = self.db.execute(
            "SELECT id FROM edges WHERE edge_type=? AND source_id=? AND target_id=? AND properties=?",
            (edge_type, source_id, target_id, json.dumps(properties, sort_keys=True)),
        ).fetchone()
        return int(row["id"])

    def _reachable(self, start: str, goal: str, edge_type: str) -> bool:
        pending, seen = [start], set()
        while pending:
            node = pending.pop()
            if node == goal:
                return True
            if node in seen:
                continue
            seen.add(node)
            pending.extend(row[0] for row in self.db.execute("SELECT target_id FROM edges WHERE edge_type=? AND source_id=?", (edge_type, node)))
        return False

    def write_claim(self, statement: str, sources: list[SourceRef], confidence: float, run_id: str, mentions: list[str], **extra: Any) -> str:
        if not sources:
            self._violate("claim_provenance", "sources must be non-empty")
        if any(not source.span.strip() for source in sources):
            self._violate("claim_span", "every SourceRef must carry a non-empty span")
        run = self.get_node(run_id)
        if run is None or run.node_type != "Run":
            self._violate("claim_run", f"created_by_run {run_id!r} is not a Run")
        for source in sources:
            node = self.get_node(source.source_id)
            if node is None or node.node_type != "Source":
                self._violate("claim_source", f"{source.source_id!r} is not a Source")
        for entity_id in mentions:
            node = self.get_node(entity_id)
            if node is None or node.node_type != "Entity":
                self._violate("claim_mention", f"{entity_id!r} is not an Entity")
        identity = json.dumps([statement, run_id, [x.model_dump() for x in sources], extra], sort_keys=True)
        claim_id = f"clm_{hashlib.sha256(identity.encode()).hexdigest()[:20]}"
        props = {"id": claim_id, "statement": statement, "confidence": float(confidence), "created_by_run": run_id, **extra}
        self._validate_node("Claim", props)
        with self.db:
            self.db.execute("INSERT INTO nodes(id,node_type,properties) VALUES(?,?,?)", (claim_id, "Claim", json.dumps(props, sort_keys=True)))
            for source in sources:
                self.db.execute(
                    "INSERT INTO edges(edge_type,source_id,target_id,properties) VALUES(?,?,?,?)",
                    ("supports", claim_id, source.source_id, json.dumps({"span": source.span}, sort_keys=True)),
                )
            for entity_id in mentions:
                self.db.execute(
                    "INSERT INTO edges(edge_type,source_id,target_id,properties) VALUES(?,?,?,?)",
                    ("mentions", claim_id, entity_id, "{}"),
                )
        if not self.provenance_edges(claim_id):
            self._violate("claim_provenance_invariant", f"claim {claim_id} has no supports/derived_from edge")
        return claim_id

    def supersede_claim(self, old_claim_id: str, statement: str, sources: list[SourceRef], confidence: float, run_id: str, mentions: list[str], **extra: Any) -> str:
        old = self.get_node(old_claim_id)
        if old is None or old.node_type != "Claim":
            self._violate("supersede_target", f"{old_claim_id!r} is not a Claim")
        new_id = self.write_claim(statement, sources, confidence, run_id, mentions, **extra)
        self.write_edge("supersedes", new_id, old_claim_id)
        return new_id

    def provenance_edges(self, claim_id: str) -> list[EdgeRecord]:
        return self.edges(source_id=claim_id, edge_types={"supports", "derived_from"})

    def nodes(self, node_type: str | None = None) -> list[NodeRecord]:
        rows = self.db.execute("SELECT * FROM nodes" + (" WHERE node_type=?" if node_type else ""), ((node_type,) if node_type else ())).fetchall()
        return [NodeRecord(id=r["id"], node_type=r["node_type"], properties=json.loads(r["properties"])) for r in rows]

    def edges(self, source_id: str | None = None, target_id: str | None = None, edge_types: set[str] | None = None) -> list[EdgeRecord]:
        clauses, values = [], []
        if source_id:
            clauses.append("source_id=?"); values.append(source_id)
        if target_id:
            clauses.append("target_id=?"); values.append(target_id)
        if edge_types:
            clauses.append("edge_type IN (%s)" % ",".join("?" for _ in edge_types)); values.extend(sorted(edge_types))
        sql = "SELECT * FROM edges" + ((" WHERE " + " AND ".join(clauses)) if clauses else "")
        return [EdgeRecord(id=r["id"], edge_type=r["edge_type"], source_id=r["source_id"], target_id=r["target_id"], properties=json.loads(r["properties"])) for r in self.db.execute(sql, values)]

    def current_claims(self) -> list[NodeRecord]:
        return [node for node in self.nodes("Claim") if not self.edges(target_id=node.id, edge_types={"supersedes"})]

    def violations(self) -> list[dict]:
        return [dict(row) for row in self.db.execute("SELECT * FROM violations ORDER BY id")]
