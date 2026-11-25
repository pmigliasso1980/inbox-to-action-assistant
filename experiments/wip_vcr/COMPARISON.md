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

| Run | Verified count | Activated count | Exact verified-to-activated ratio | VCR calculation |
|---|---:|---:|---:|---|
| Unconstrained | 1 | 3 | 1:3 | (1 verified / 3 activated) × 100 = 33.333…% |
| WIP=1 | 2 | 2 | 2:2 | (2 verified / 2 activated) × 100 = 100% |

The baseline activated health, queue, and version at actions 1, 3, and 5.
Its only successful verification was health at action 8. The treatment
activated health and queue and verified each once, as shown below.

| Run | Actions | Peak WIP | Response fixture lines | Elapsed |
|---|---:|---:|---:|---:|
| Unconstrained | 8 | 3 | 3 | 3627.13 ms |
| WIP=1 | 8 | 1 | 2 | 47.12 ms |

Each finish writes a JSON response fixture. A successful HTTP request and
matching jq assertion are required for `passing`. The unconstrained run left
queue and version active with placeholder responses. The treatment left
version pending, with neither activation nor verification counted for it.

## WIP=1 treatment event sequence

These rows transcribe the recorded `wip_1.events` in [evidence.json](evidence.json).

| Action # | Feature | Operation | Feature state after action | Active count after action | Verification evidence |
|---:|---|---|---|---:|---|
| 1 | health | activate | active | 1 | |
| 2 | health | draft | active | 1 | |
| 3 | health | finish | active | 1 | |
| 4 | health | verify | passing | 0 | Exit code 0, jq output `true` |
| 5 | queue | activate | active | 1 | |
| 6 | queue | draft | active | 1 | |
| 7 | queue | finish | active | 1 | |
| 8 | queue | verify | passing | 0 | Exit code 0, jq output `true` |

Health was the only active feature through action 3. Action 4 recorded
its passing check and released the slot before queue was activated at
action 5. Queue held the slot through action 7 and released it after the
passing check at action 8. Version stayed pending throughout.

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
