# Provenance Graph

## Backend boundary

`GraphStore` uses SQLite for local development, committed fixtures, and tests.
ADR-002 selects PostgreSQL for production. Neo4j is not required by the current
access patterns or measured scale.

## Executable schema

The five node types are `Entity`, `Claim`, `Source`, `Artifact`, and `Run`.
The five edge types are `mentions`, `supports`, `contradicts`, `derived_from`,
and `supersedes`. `NODE_SCHEMA` and `EDGE_ENDPOINTS` in `store.py` are the source
of truth.

## Invariants

- Entity ids are deterministic canonical ids; aliases are preserved.
- Claims can only be written through `write_claim`.
- Every claim has at least one `supports` or `derived_from` edge.
- Every supporting edge contains a nonblank verbatim span.
- Confidence stays within `[0, 1]`.
- Updates append a new claim and add `supersedes`.
- Supersession connects the same node type and cannot form a cycle.
- Current queries exclude superseded claims by default.
- Contradictions are preserved rather than silently resolved.

The rule “every graph claim requires source provenance” was converted from an
instruction into `test_repository_graph_has_no_unprovenanced_claims` in
`test_repository_contracts.py`. This prevents documentation drift: weakening
the prose cannot make invalid graph data pass CI.

## Safe change workflow

```bash
python3 -m pytest -q graph/test_store.py graph/test_repository_contracts.py
python3 graph/seed.py
python3 -m pytest -q graph
```

Do not reseed `graph/knowledge.db` without reviewing the generated verification
summary and ensuring historical ids referenced by reports remain valid.
