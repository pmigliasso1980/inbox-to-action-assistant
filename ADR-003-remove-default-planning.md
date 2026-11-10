# ADR-003 — Remove planning from the default review path

## Context

The production audit found that the planning stage reduced full-set mean score
from 0.8833 to 0.8436 while adding $0.03020 per item and raising p95 latency to
40.10 seconds. The 0.0398 score change is within the 0.0667 empirical noise
floor, so cost per point is undefined rather than favorable.

## Decision

Remove planning from the default code-review path. Keep it as an explicitly
routed capability for tasks whose deterministic complexity signal requires
dependencies, three or more tool steps, or replanning.

## Expected effect and verification

Expected savings are $0.03020/item and roughly 33 seconds of p95 latency versus
the measured planning configuration, without a distinguishable quality loss.
Verify on the 20-item regression set and a routed complex-task slice; require
score to remain within the 0.0667 noise floor and monitor escalation rate.

## Rollback

Re-enable the planner route behind its existing configuration flag. No stored
data migration is required because plans and artifacts remain additive logs.
