# Module 8.1 — Graph Store Report

## Backend and scope

The backend is **SQLite**: zero service setup, inspectable with standard tools, transactional, and fully
adequate for the course’s five-node/five-edge schema. This is a technical exercise rather than a
reversal of ADR-001: production remains on an append-only state file until graph criteria bind, but the
store is available for Modules 9–10.

Schema definitions in `graph/store.py` are executable data. Nodes are `Entity`, `Claim`, `Source`,
`Artifact`, and `Run`; edges are `mentions`, `supports`, `contradicts`, `derived_from`, and
`supersedes`. Claim creation has no generic bypass: `write_node("Claim", ...)` is rejected and
`write_claim` requires a non-empty `SourceRef` list with exact spans. Claims and artifacts are
additive; supersession creates a new node and edge, and current versions are determined by traversal.

No extra node or edge types were introduced. Optional Claim properties—`subject`, `predicate`,
`object`, and `claim_kind`—pay for the ADR’s changed-finding and rejected-assumption queries without
expanding the schema.

## Canonical identifiers

Normalization lowercases; trims whitespace; converts punctuation, underscores, and path separators to
spaces; removes repeated whitespace; strips `./`, `src/`, `lib/`, and `app/` path prefixes; strips
ticket/issue/bug prefixes; and removes legal suffixes such as Inc, Ltd, Corp, and LLC. The normalized
identity, entity type, and identity-bearing attributes are hashed. Surface forms remain in `aliases`.

Worked merge:

```text
range_total.py
src/range_total.py    → ent_ad2b3ac9a5c370dfeea7
RANGE TOTAL.PY
```

The node retains all three aliases. Tests also prove `Acme Inc.`, `ACME`, and `acme corporation` merge
without discarding their original forms.

## Seed verification

The seed uses the first 15 frozen evaluation documents and creates four provenance-backed claims per
document, plus a three-version history and a retained contradiction.

| Check | Result |
|---|---:|
| Entity nodes | 30 |
| Claim nodes | 63 |
| Source nodes | 15 |
| Artifact nodes | 15 |
| Run nodes | 1 |
| `mentions` edges | 123 |
| `supports` edges | 63 |
| `contradicts` edges | 1 |
| `derived_from` edges | 15 |
| `supersedes` edges | 2 |
| Claims with no provenance | **0** |
| Schema violations during seeding | **0** |
| Entities with multiple aliases | 1 |
| Current claims / total claims | 61 / 63 |
| Current-flag/traversal disagreements | **0** |
| Contradiction pairs | 1 |

## Seven typed query outputs

Full typed JSON is in `runs/graph-store-verification.json`. Representative output:

1. `current_claims_about(range_total)` returns the current line-support claim, current off-by-one
   version, and conflicting “no off-by-one” claim; superseded versions are absent.
2. `provenance_of(current_off_by_one)` returns `source-001` and exact span
   `for i in range(n + 1):`.
3. `contradictions()` returns
   `clm_7d290d5ce728fe0abb66 ↔ clm_b642806a2803eef13e60`.
4. `history_of(current_off_by_one)` returns, oldest to newest: “contains off_by_one,” “contains an
   off-by-one loop boundary,” then “iterates through n inclusive.”
5. `changed_findings(range_total)` returns four Run-linked records with prompt version
   `graph-seed-v1`, including old, current, and conflicting statements.
6. `decision_provenance(current_off_by_one)` returns the Claim, canonical file Entity, Source, exact
   support edge/span, and the superseded claim id.
7. `rejected_assumptions(config.py)` returns the retained rejected-assumption Claim about the
   swallowed-exception supporting line.

## Guarantees

Tests fail if canonical ids diverge, aliases disappear, a claim lacks provenance, confidence leaves
[0,1], endpoints are illegal, node/edge types are unknown, supersession mutates history, or a cycle is
created. The seeded database is `graph/knowledge.db`; regeneration is deterministic with
`PYTHONPATH=. python3 graph/seed.py`. New API cost: **$0.00**.

