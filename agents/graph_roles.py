"""Role registry and code-enforced graph access scopes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from graph.queries import changed_findings, current_claims_about, decision_provenance
from graph.store import GraphStore, SourceRef


@dataclass(frozen=True)
class RoleSpec:
    prompt_path: str
    read_scope: Callable[[GraphStore, str], list]
    write_nodes: frozenset[str]
    write_edges: frozenset[str]
    tools: tuple[str, ...]
    effort: str


def architect_read(store: GraphStore, entity_id: str) -> list:
    return current_claims_about(store, entity_id)


def tech_lead_read(store: GraphStore, entity_id: str) -> list:
    return [x for x in current_claims_about(store, entity_id) if x.properties.get("predicate") == "has_defect"]


def developer_read(store: GraphStore, entity_id: str) -> list:
    claims = current_claims_about(store, entity_id)
    return [decision_provenance(store, claim.id) for claim in claims[:3]]


def historian_read(store: GraphStore, entity_id: str) -> list:
    return changed_findings(store, entity_id)


ROLES = {
    "architect": RoleSpec("agents/roles/architect.md", architect_read, frozenset({"Artifact"}), frozenset({"derived_from"}), (), "high"),
    "tech_lead": RoleSpec("agents/roles/tech_lead.md", tech_lead_read, frozenset({"Claim"}), frozenset({"supports", "mentions", "contradicts", "supersedes"}), (), "medium"),
    "developer": RoleSpec("agents/roles/developer.md", developer_read, frozenset({"Artifact"}), frozenset({"derived_from"}), ("local_patch",), "medium"),
    "historian": RoleSpec("agents/roles/historian.md", historian_read, frozenset(), frozenset(), (), "low"),
}


@dataclass
class ScopedGraph:
    store: GraphStore
    role: str
    events: list[dict] = field(default_factory=list)

    @property
    def spec(self) -> RoleSpec:
        return ROLES[self.role]

    def read(self, entity_id: str) -> list:
        result = self.spec.read_scope(self.store, entity_id)
        self.events.append({"kind": "read", "role": self.role, "query": self.spec.read_scope.__name__, "result_size": len(result)})
        return result

    def _deny(self, kind: str, value: str) -> None:
        event = {"kind": "scope_violation", "role": self.role, "scope": kind, "value": value}
        self.events.append(event)
        raise PermissionError(f"{self.role} cannot write {kind} {value}")

    def write_artifact(self, props: dict, source_id: str) -> str:
        if "Artifact" not in self.spec.write_nodes:
            self._deny("node", "Artifact")
        node_id = self.store.write_node("Artifact", props)
        if "derived_from" not in self.spec.write_edges:
            self._deny("edge", "derived_from")
        edge_id = self.store.write_edge("derived_from", node_id, source_id, {"created_by_role": self.role})
        self.events.append({"kind": "write", "role": self.role, "node_ids": [node_id], "edge_ids": [edge_id]})
        return node_id

    def write_claim(self, *, statement: str, sources: list[SourceRef], confidence: float,
                    run_id: str, mentions: list[str], **extra) -> str:
        if "Claim" not in self.spec.write_nodes:
            self._deny("node", "Claim")
        claim_id = self.store.write_claim(
            statement, sources, confidence, run_id, mentions,
            created_by_role=self.role, **extra,
        )
        self.events.append({"kind": "write", "role": self.role, "node_ids": [claim_id], "edge_ids": []})
        return claim_id
