# ADR-CAPSTONE — Ship a gated tool-and-graph chain

## 1. Context

Incident commanders need structured post-mortem summaries with correct owners
and recurrence evidence. Wrong outputs are consequential but remain subject to
human review.

## 2. Measured progression

Two baselines scored 0.50 and 0.48 (noise 0.02). Reflection reached 0.65, the
confirmed owner tool 0.85, and graph memory 0.95. Repeat-pattern score improved
from 0.70 to 0.90 with graph memory; first encounters stayed at 1.00.

## 3. Current architecture

Strict input → deterministic extraction/reflection → read-only owner tool with
confirmation → provenance-backed recurrence query/write → strict output.

## 4. Decision-rule assessment

Use deterministic software for known mappings and validation, graph retrieval
for durable cross-session facts, and human review for operational decisions.
There is no unbounded autonomous loop.

## 5. Criteria assessment

Planning has no dependency graph to manage. Additional agents have no measured
distinct stance. Graph memory is justified by a +0.20 repeat-pattern lift and
50% cross-session read rate.

## 6. Anti-pattern audit

No premature planner, permanent agent team, transcript forwarding, or phantom
graph. Writes have provenance; reads are measured; tools are read-only.

## 7. Decision

Ship the gated chain with the graph enabled for recurrence. Skip planning,
multi-agent review, and routing. Require human approval before an output changes
an incident's official severity, owner, or remediation record.

## 8. Consequences

The system is cheap, reproducible, and auditable, but its cause vocabulary is
bounded and five verification details remain incomplete. Rollback disables the
graph lookup and returns to the 0.85 tool configuration without data loss;
claims remain additive audit history.
