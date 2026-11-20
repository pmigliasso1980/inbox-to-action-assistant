# Knowledge Visibility Gap

A decision counts as visible when a fresh reader can reach an explicit current statement from `README.md` or `AGENTS.md` within two links. The gap formula is `1 - visible decisions / total decisions`.

| Decision | Visible before? | After evidence |
|---|---|---|
| Python 3.11+ runtime | Yes | `AGENTS.md` |
| Pydantic 2 strict contracts | Yes | `AGENTS.md` |
| SQLite local/test graph | Yes | `graph/README.md` |
| PostgreSQL production graph target | Yes | `ADR-002-graph-backend.md` |
| Offline replay and paid calls opt-in | Yes | `docs/REPOSITORY_GUIDE.md` |
| Deterministic gates before model evaluation | Yes | `agents/README.md` |
| Every claim has provenance and span | Yes | `graph/README.md` |
| Graph updates are additive supersessions | Yes | `graph/README.md` |
| Planning removed from default path | No | `ADR-003-remove-default-planning.md` |
| Large artifact bodies stay outside graph | No | `docs/REPOSITORY_GUIDE.md` |
| Orchestrator uses bounded graph queries | No | `agents/README.md` |
| Cached input is accounted separately | Yes | `reports/README.md` |
| External side effects require human approval | Yes | `docs/REPOSITORY_GUIDE.md` |
| Current verified entry points are task-specific | No | `docs/REPOSITORY_GUIDE.md` |
| Tests/ADRs/generated evidence have authority order | No | `docs/REPOSITORY_GUIDE.md` |

## Calculation

- Before: `10 / 15` visible; gap = `1 - 10/15` = **33.3%**.
- After: `15 / 15` visible; gap = `1 - 15/15` = **0.0%**.
- Improvement: **33.3% percentage points**.
