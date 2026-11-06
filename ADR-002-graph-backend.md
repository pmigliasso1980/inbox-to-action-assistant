# ADR-002: Use PostgreSQL for the Production Graph Backend

- **Status:** Accepted
- **Date:** 2026-11-05
- **Decision owner:** Repository maintainer
- **Related decisions:** `ADR-001-architecture.md`

## Context

Module 8 implements a five-node, five-edge knowledge graph in SQLite. SQLite is appropriate for local
development, tests, course evaluation, reproducible demonstrations, and an isolated single-process
pilot. It keeps the schema and data-quality work independent of infrastructure and currently handles
the small seeded corpus without operational overhead.

The product is intended to reach production later. A hosted, multi-user deployment changes the
requirements: multiple application instances may read and write concurrently; backups and point-in-time
recovery become mandatory; access must be controlled centrally; schema migrations must be coordinated;
and graph state must be observable and highly available. SQLite should not become the production
backend merely because it was the first implementation.

ADR-001 still applies: the graph is not yet required in the shipped decision path. This ADR chooses the
backend **if and when graph-backed functionality is promoted to production**.

## Decision

Use **PostgreSQL as the production graph backend**. Retain SQLite for local development, automated
tests, offline evaluation, and repository fixtures.

PostgreSQL will represent the current graph contract with relational `nodes` and `edges` tables,
typed columns for identifiers and relationship endpoints, JSONB for type-specific properties, foreign
keys, uniqueness constraints, transactional additive writes, and indexes for the seven established
queries. Recursive CTEs will support supersession history and bounded traversal. A managed PostgreSQL
service is preferred for production backups, patching, monitoring, and failover.

This decision does not authorize a production migration today. It records the target so new graph code
preserves portability and the eventual migration is planned rather than improvised.

## Why PostgreSQL

- The existing graph is modest and its known queries are shallow and well-defined.
- Transactions, foreign keys, constraints, and concurrent writes match the store’s correctness needs.
- Managed PostgreSQL provides mature backup, recovery, observability, authentication, and high
  availability options.
- JSONB preserves flexible type-specific properties while canonical ids and edge endpoints remain
  strongly indexed.
- The broader product will likely need ordinary relational data—users, review queues, approvals,
  tenancy, and audit records—alongside graph relationships.
- Operational familiarity and ecosystem support reduce production risk compared with introducing a
  dedicated graph service before graph-specific scale is proven.

## Alternatives considered

### SQLite in production

Rejected for the expected hosted, multi-instance product. SQLite remains excellent for local and
single-process use, but its deployment model complicates shared concurrent writes, centralized access
control, high availability, and managed recovery. It may still support an explicitly local desktop
edition.

### Neo4j

Deferred, not rejected permanently. Neo4j offers excellent variable-depth traversal, Cypher,
visualization, and graph algorithms. Current evidence does not show that those capabilities outweigh a
second production datastore and its operational cost. Reconsider Neo4j if traversal becomes the core
workload and PostgreSQL recursive queries or indexing fail measured service objectives.

### PostgreSQL plus a graph extension

Not required initially. Extensions may improve graph syntax or vector retrieval, but they add version
and hosting constraints. Adopt one only after a measured query requires it and the managed provider
supports it reliably.

## Portability requirements

To keep the migration safe:

1. Consumers depend on a backend-neutral `GraphStore` contract, not SQLite SQL.
2. Canonical ids, node/edge types, additive supersession, provenance rules, and typed query results are
   identical across backends.
3. Backend contract tests run against SQLite and PostgreSQL with the same fixtures.
4. Schema changes use versioned migrations; application startup never silently rewrites history.
5. Nodes and edges support a versioned JSONL export/import format for migration and recovery.
6. Claim and Artifact writes remain append-only; corrections create `supersedes` edges.
7. Source hashes and Run configuration fields remain mandatory.
8. PostgreSQL constraints supplement—not replace—the application validator and audit suite.

## Migration plan

1. Extract the current SQLite implementation behind a formal store protocol.
2. Add a PostgreSQL adapter and migrations for nodes, edges, violations, and required indexes.
3. Run the existing invariant and seven-query test suites against both backends.
4. Export the SQLite graph to versioned JSONL, import into a staging PostgreSQL database, and compare
   counts, canonical ids, provenance, current-version traversal, contradictions, and query output.
5. Load-test production-shaped read/write concurrency and record p50/p95 latency.
6. Rehearse backup restoration, migration rollback, and dual-read comparison.
7. Freeze writes briefly, perform a final incremental transfer, switch reads, then switch writes.
8. Keep the SQLite/export snapshot until post-migration audits pass.

Dual-write is not the default migration strategy because it creates another consistency problem. Use it
only if a no-downtime requirement outweighs the additional reconciliation risk.

## Promotion and reconsideration triggers

Migration to PostgreSQL is required before graph state becomes shared production data or before more
than one application instance writes it. It is also triggered by requirements for centralized
authorization, point-in-time recovery, managed failover, or production retention guarantees.

Reconsider Neo4j or another graph-native service only when measurements show one or more of:

- variable-depth traversals dominate the workload;
- graph queries cannot meet their agreed p95 latency after PostgreSQL indexing and query tuning;
- graph size and fan-out make recursive CTEs operationally expensive;
- graph algorithms or interactive exploration become product capabilities rather than developer tools.

The decision must be revisited with real query traces, graph size, concurrency, and cost—not database
preference alone.

## Consequences

Positive consequences include a clear production target, strong transactional guarantees, one likely
datastore for relational and graph-adjacent product state, and a mature operational path. SQLite keeps
local development inexpensive and fast.

Costs include maintaining two adapters, backend contract tests, migrations, and staging infrastructure.
Some graph queries will be more verbose than Cypher. The team must monitor query plans and resist
placing unconstrained properties in JSONB when a stable indexed column is appropriate.

This ADR commits the product to PostgreSQL for the first graph-backed production deployment while
keeping Neo4j as an evidence-triggered future option.

