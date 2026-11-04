# Lab 3.2 report — fallbacks and permission boundaries

## Reproducible fallback study

Ten fixed items ran under all six failure modes with implicit and explicit policies. The explicit policy retries retryable primary failures twice, then supplies the weaker static-linter fallback; auth, empty, and garbage route directly after failure or confirmation rejection.

| Mode | Implicit completion / fallback / score | Explicit completion / fallback / score |
|---|---:|---:|
| none | 100% / 0% / 0.3667 | 100% / 50% / 0.3667 |
| rate limit | 100% / 0% / 0.2833 | 100% / 100% / 0.3500 |
| timeout | 100% / 10% / 0.4000 | 100% / 100% / 0.3500 |
| auth | 100% / 0% / 0.2500 | 100% / 100% / 0.3333 |
| empty | 90% / 20% / 0.4074 | 100% / 100% / 0.4500 |
| garbage | 100% / 0% / 0.3000 | 90% / 90% / 0.5000 |

All ungrounded-answer rates were **0%** because the model obtained primary/fallback evidence or read canonical source. `read_code` counts as grounding but not as invocation of the designated `run_linter` fallback. Implicit recovery therefore often completed honestly without that fallback. Explicit routing made fallback behavior reproducible and improved rate-limit, auth, empty, and garbage score, but not timeout. It improved empty completion from 90% to 100%; explicit garbage had one invalid-JSON completion failure, demonstrating that grounded evidence does not guarantee protocol compliance.

Empty and garbage were confirmation tests, not exceptions. Both failed relevance/emptiness confirmation and routed away from the primary. A representative recovery is the explicit rate-limit trace: two retryable failures followed by a confirmed linter result. The study produced no confidently ungrounded response to quote—the control prevented the target failure. The closest negative case is implicit empty item 010, which failed valid JSON and was counted incomplete rather than relabelled as success.

The full 120-item matrix cost **$2.768370**. Per-item traces and configuration summaries are under `runs/fallbacks/`; `runs/fallbacks/summary.json` is the compact table.

## Permission boundary proof

`post_review_comment` is a strict-schema write tool backed by a separate `WritableCommentStore`. Read tools receive `ReadOnlyReviewStore`, which exposes no append/write method. The callback gate supports `auto_approve`, `auto_deny`, and interactive modes. Dry-run validates and audits the preview without writing.

| Required case | Observed behavior |
|---|---|
| Normal, auto-approve | One local comment written; approval and successful validation audited. |
| Same write, auto-deny | No second comment; explicit `user declined` error returned; denial audited. |
| Invalid severity | Rejected before append; validation failure audited. |
| `../../etc/passwd` | Direct hostile tool call rejected as non-canonical; attempt audited. |

`runs/comments.jsonl` contains exactly the approved write. `runs/audit.jsonl` contains all four attempts, including denial and failures. Each line includes timestamp, run/item IDs, full arguments, gate decision, validation result, and outcome.

The junior-engineer analogy holds for least privilege, review before write, dry runs, validation, and an incident-ready audit trail. It breaks on scale: an agent can issue many destructive calls without hesitation, social feedback, fatigue, or an intuitive sense of blast radius. Controls must therefore be enforced in code and per action; instructions and presumed judgment are not permission boundaries.
