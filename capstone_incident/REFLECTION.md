# Capstone Reflection

The owner-directory tool delivered the best return: +0.20 score for a local,
read-only lookup with negligible latency and no token cost. It worked because
ownership is deterministic data, not a judgment task.

Reflection disappointed relative to expectation. It added +0.15, but its generic
remediation mapping missed the five service-specific verification requirements.
The issue is not insufficient reasoning effort; the output contract combines
the action and its proof into one string.

From the start, I would model remediation and verification method separately.
That would make the missing proof mechanically visible and avoid asking an LLM
judge to interpret whether a remediation is sufficiently testable.

One course claim my measurements do not support universally is that a
multi-agent system provides better control than a single agent with tools. On
this task, there was no measured distinct error class for another role. A gated
single path plus deterministic data and cross-session memory was cheaper and
more legible. Multi-agent specialization remains useful when the task genuinely
contains independent stances; it is not an intrinsic maturity upgrade.
