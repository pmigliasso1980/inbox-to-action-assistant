# Architecture Decision Index

| Decision | Status | Consequence | Evidence |
|---|---|---|---|
| [ADR-001](../ADR-001-architecture.md) | Accepted | Use the smallest measured architecture; graph queries are explicit. | Architecture audit |
| [ADR-002](../ADR-002-graph-backend.md) | Accepted | SQLite local/test; PostgreSQL production target. | Graph store report |
| [ADR-003](../ADR-003-remove-default-planning.md) | Accepted | Planning is routed, not a default stage. | +$0.0302/item; delta inside noise |
| [Capstone ADR](../capstone_incident/ADR-CAPSTONE.md) | Accepted for capstone | Gated tool-and-graph chain; human approval for official changes. | 0.95 final; +0.20 repeat lift |

## Additional measured decisions

- Keep graph claims, sources, entities, and run audit metadata.
- Remove large artifact bodies from the graph; retain external content refs.
- Use bounded graph synthesis because its context slope measured 0.162 tokens per
  worker versus 766.405 for transcript forwarding.
- Keep paid provider calls opt-in; deterministic and frozen replays are the
  default evidence path.

Superseding an accepted decision requires a new ADR. Do not edit an old ADR to
erase the context or measurement that originally justified it.
