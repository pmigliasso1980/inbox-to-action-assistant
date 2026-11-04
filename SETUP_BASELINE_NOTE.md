# Lab 1.1 setup and effort baseline

1. Python version: 3.11.3.
2. Anthropic SDK version: 0.86.0; project requirement is `anthropic>=0.60`.
3. Model used consistently: `claude-opus-5`.
4. The API key is loaded from an ignored `.env` file and is not committed.
5. Fixed prompt: “In one sentence, state what an agentic workflow is.”
6. Token count before inference: 23 input tokens.
7. Low effort used 23 input tokens and 116 output tokens.
8. Low-effort cost: `(23 × $5 + 116 × $25) / 1M = $0.003015`.
9. High effort used 23 input tokens and 116 output tokens.
10. High-effort cost: `(23 × $5 + 116 × $25) / 1M = $0.003015`.
11. Combined verification cost: $0.006030.
12. Both answers correctly defined an agentic workflow as a multi-step, tool-capable process.
13. High effort did not produce a materially better answer for this trivial prompt.
14. The result supports using low effort for the Module 1 baseline.
15. `UsageLedger` also writes timestamped JSONL records to `runs/usage.jsonl`.
16. The Anthropic SDK retains its built-in retry policy with `max_retries=2`.
