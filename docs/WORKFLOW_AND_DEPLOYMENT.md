# Workflow and deployment design

## 1. Audit: the real workflow

### Current state

A person reads an incoming message, works out whether it matters, identifies actions and dates, decides
whether to reply, drafts language, and tracks the commitment somewhere else—or remembers it. The clean
description hides the cases that consume attention:

- forwarded threads contain old and superseded instructions;
- dates are relative, vague, contradictory, or already past;
- the apparent owner is not the person receiving the message;
- attachments are mentioned but unavailable;
- urgency language may not correspond to a real action;
- a draft can accidentally promise work or imply that an action already happened;
- newsletters, acknowledgments, and duplicates should create no task;
- operational, financial, legal, medical, or destructive requests need a stronger boundary;
- message content may contain prompt-injection text that is data, not an instruction to the system.

The highest-value first scope is not autonomous email. It is reducing review effort and missed
commitments while keeping the user in control.

### Target state and judgment allocation

| Stage | Deterministic software | LLM judgment | Human responsibility |
|---|---|---|---|
| Intake | Validate fields, deduplicate, assign correlation ID | None | Correct source/connectivity problems |
| Analysis | Validate schema, ground evidence, resolve permitted dates, enforce priority | Interpret intent, summarize, extract candidate actions | Correct ambiguous facts and ownership |
| Draft | Require a draft only when needed; block unsupported commitments | Produce concise language in the source language | Edit wording and decide whether it represents the user |
| Review | Enforce authorization invariants and record risks | Semantic consistency and safety review | Approve, revise, or reject |
| Persist | Transactional message/action/event writes | None | Supply correction/decision notes |
| External action | Approval check, idempotency, API call, reconciliation | None by default | Trigger or perform the final send/action |

An LLM is justified only where language interpretation or composition is genuinely non-deterministic.
It is not used for database writes, calendar arithmetic, authorization, retry policy, or approval.

## 2. ROI and priority

| Opportunity | Expected value | Risk | Decision |
|---|---|---|---|
| Extract candidate actions and evidence | High review-time saving; reduces missed commitments | Medium: omission or hallucination | Build with schema, grounding, evals, and human review |
| Resolve simple relative dates | Moderate consistency gain | Low when grounded; high when ambiguous | Deterministic resolver; escalate ambiguity |
| Draft replies | Moderate time saving | Medium: unsupported promises or tone | Build as draft only; never auto-send |
| Auto-send ordinary replies | Additional convenience | High: external side effect and reputational risk | Out of scope until shadow evidence supports it |
| Execute operational/financial actions | Potentially high | Very high and context-dependent | Out of scope; require purpose-built controls |
| Replace the inbox/task platform | Low incremental value and high adoption cost | High | Do not do; integrate with existing systems |

Pilot economics should measure median review minutes per message, action precision/recall, missed-action
rate, correction rate, repeat use, model cost per processed message, and support time. Revenue impact is
not claimed for this personal workflow; the initial business case is cost/time saving and risk
mitigation.

## 3. Evals

The evaluation harness separates deterministic guarantees from variable model behavior:

1. Unit tests cover exact policies and state transitions.
2. Structured fixtures cover normal, edge, ambiguous, multilingual, and high-risk cases.
3. Live evals exercise the full analysis/draft/review chain.
4. Repeated runs measure unstable high-risk behavior.
5. Shadow evaluation uses only synthetic or anonymized messages before any external integration.

Pass/fail dimensions include extraction, date grounding, priority, reply need, draft quality, safety,
and persistence. Safety is a separate release gate. Detailed taxonomy, commands, and future metrics are
in [`EVALUATION_STRATEGY.md`](EVALUATION_STRATEGY.md).

## 4. Deployment on existing systems

### Integration points

- **Existing mailbox or form:** a read-only adapter provides message ID, sender, subject, body, and
  received timestamp. It stores the provider message ID as the idempotency key.
- **Assistant service:** the existing `InboxService` remains the application boundary. Provider-specific
  code does not leak into agents or policies.
- **Model provider:** the Responses API returns Pydantic-validated structures. The configured preferred
  model falls back only when access is denied.
- **Database:** SQLite supports the local single-user pilot. A production deployment uses a managed
  relational store with transactions, encryption, backups, retention, and least-privilege identities.
- **Review surface:** a UI or the current CLI exposes source, evidence, confidence, draft, risks, and
  history. It calls `revise`, `approve`, or `reject`; it does not bypass the service.
- **Task/draft system:** a future adapter may create a draft or task only after approval. It records the
  external object ID and reconciles before retrying.
- **Observability:** structured logs carry the correlation ID, stage, duration, model, retry count,
  error category, token/cost data, and decision. Message content is redacted from ordinary logs.

### Rollout

1. **Sandbox:** synthetic data, deterministic tests, and live eval fixtures.
2. **Shadow:** anonymized real-shaped messages; compare with human labels; no external writes.
3. **Reviewed pilot:** bounded users receive analyses and drafts in the review queue.
4. **Integration:** create external drafts/tasks after explicit approval, using idempotency and
   reconciliation.
5. **More autonomy:** considered per action type only after sufficient volume meets quality, safety,
   cost, and audit gates. Sending remains human-controlled by default.

Rollback is disabling the ingestion/side-effect adapter while retaining audit data. The user's normal
inbox workflow continues because the design does not replace it.

## 5. Failure handling

| Failure | Detection | Response | Retry? |
|---|---|---|---|
| Empty or invalid input | Local validation | Reject with actionable error | No |
| Provider rate limit, timeout, or 5xx | Typed provider error | Bounded exponential backoff with jitter; preserve correlation ID | Yes, bounded |
| Model unavailable to API key | 403 from model endpoint | Try the allow-listed fallback models | Only fallback |
| Malformed or missing structured output | Pydantic/parser or null result | Fail closed and place the item in manual review | At most one controlled regeneration in a production adapter |
| Unsupported evidence/date | Deterministic grounding policy | Lower confidence or remove the date; show reason to reviewer | No |
| Ambiguous instruction | Policy/model confidence and reviewer | Mark `needs_confirmation`; do not infer an external action | No |
| Duplicate webhook/message | Existing idempotency key | Return the prior result | No |
| Database write failure | Transaction error | Roll back; do not acknowledge ingestion; alert | Yes if transient |
| External create times out | Missing response with known idempotency key | Query/reconcile before retrying | Conditional |
| Unsafe or unauthorized action | Risk rule or missing approval | Block and route to human | No |
| Retry budget exhausted | Attempt counter | Dead-letter with source reference, error category, and next owner | No automatic retry |

The example in [`../examples/integration_strategy.py`](../examples/integration_strategy.py) makes this
control flow visible without adding an external integration or side effect to the current product.

## 6. Ownership and boundaries

- The product owner owns workflow definitions, quality thresholds, and rollout decisions.
- The engineering owner owns service reliability, adapters, database migrations, and incident response.
- A reviewer owns every final decision and correction.
- The model never owns a commitment, an approval, or an external side effect.
- No private inbox content belongs in source control or evaluation fixtures.
