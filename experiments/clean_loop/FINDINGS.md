# Verification debt and clean exit

The first generator exited 0 with an empty index. Treating that exit as
completion would have left both required links unchecked. The evaluator
caught the coverage gap against its manifest. The second attempt checked
both required targets with zero missing, broken, unexpected, malformed, or
duplicate links. A maintainer still needs to confirm that the manifest is
current and review the labels and report contents before applying the snippet.
The run used zero paid model calls.

## Five-condition exit proof

| Checklist condition | Recorded proof |
|---|---|
| Verification is current | The coordinator exited 0 on revision `1f450e2`. Evaluator exit codes were 1 and 0. |
| Worktree is accounted for | Before and after Git status outputs were empty. The temporary snapshot was removed. |
| Completed work is checkpointed | The log contains the source revision, accepted candidate, and candidate SHA-256. |
| Progress is recoverable | Both proposals and verdicts are recorded. An earlier development run failed on the Python 3.11 tar API, which the ZIP snapshot revision resolved. |
| Next action is clear | A repository maintainer reviews the accepted candidate and confirms coverage before editing the index. |

See [raw evidence](run-log.json) and [loop specification](LOOP_SPEC.md).
