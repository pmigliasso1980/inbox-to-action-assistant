# WIP=1 experiment

Both runs started with the same three pending behaviors in a blank temporary
directory. Each used an eight-action budget. An activation, draft, finish,
or verification each counts as one action. The unconstrained schedule may
switch features at any point. The treatment rejects activation while another
feature is active and records each curl/jq result before proceeding.

**VCR = (distinct activated features that passed verification ÷ distinct
features activated during the run) × 100.** A feature counts as verified
when its `verify` event records exit code 0 and state `passing`.
Active but unfinished features count in the denominator. Pending features
without an activation event are excluded.

| Run | Activated features (denominator) | Verified features (numerator) | Exact ratio | VCR |
|---|---|---|---:|---:|
| Unconstrained | health, queue, version (3) | health (1) | 1/3 | 33.33% (rounded) |
| WIP=1 | health, queue (2) | health, queue (2) | 2/2 | 100.00% |

| Run | Actions | Peak WIP | Response fixture lines | Elapsed |
|---|---:|---:|---:|---:|
| Unconstrained | 8 | 3 | 3 | 3627.13 ms |
| WIP=1 | 8 | 1 | 2 | 47.12 ms |

Each finish writes a JSON response fixture. A successful HTTP request and
matching jq assertion are required for `passing`. The unconstrained run left
queue and version active with placeholder responses. The treatment left
version pending, with neither activation nor verification counted for it.

Recalculate the counts directly from the committed event log:

```bash
jq 'to_entries[] | .key as $run | .value.events |
  ([.[] | select(.action == "activate") | .feature] | unique) as $activated |
  ([.[] | select(.action == "verify" and .exit_code == 0 and .state == "passing")
    | .feature] | unique | map(select(. as $id | $activated | index($id)))) as $verified |
  {run: $run, activated: ($activated | length), verified: ($verified | length),
   vcr_percent: (($verified | length) / ($activated | length) * 100)}' \
  experiments/wip_vcr/evidence.json
```

The initial idea, “verify the status API,” was scoped into three separate
GET contracts: health, queue count, and version. Each can pass independently
with one response assertion. See [the final feature list](feature_list.json),
[the timed event log](evidence.json), and [the reflection](REFLECTION.md).

Reproduce from the repository root with Python 3.11+, bash, curl, jq, and
permission to bind an ephemeral loopback port.

```bash
python3 experiments/wip_vcr/run.py
```

The runner resets feature states for each run. This is a controlled replay of
two predefined schedules with real verification calls. The experiment
illustrates the effect of those scheduling choices under a fixed action
budget. The single-run timings include local server startup and check
execution and do not support a general speed comparison.
