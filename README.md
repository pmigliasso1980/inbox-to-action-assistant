# Inbox-to-Action Assistant

Turn emails, messages, or notes into summaries, tasks, dates, priorities, and reviewed reply drafts.
The current version accepts manually pasted text and stores results in SQLite. It never sends messages
or performs external actions.

This project is also an FDE workflow-design case study: it shows where deterministic code, LLM
judgment, and human approval belong in a real inbox workflow, then demonstrates how to deploy that
design on top of existing systems rather than replace them.

## Current graded submission — Module 5 MCP Client

The required files are available directly at the repository root so automated graders do not need to
infer nested paths:

- [`client.py`](client.py) — connects, initializes, discovers four tools, invokes them, distinguishes
  five failure modes, and provides a reusable `run_tool` helper.
- [`server.py`](server.py) — root entry point for the persistent MCP document server.
- [`LAB_NOTES.md`](LAB_NOTES.md) — observed outputs and required analysis.

Run the submission with:

```bash
mcp-document-server/.venv/bin/python client.py
```

## Why AI belongs here

Inbox messages are unstructured: intent, implied actions, tone, and ambiguous dates cannot be handled
reliably with fixed rules alone. LLMs are useful for that narrow judgment layer. Validation, date
policy, persistence, authorization, and state transitions remain deterministic because they must be
repeatable and auditable. A human remains accountable for corrections and every final approval.

## Workflow map

| Step | Owner | Why |
|---|---|---|
| 1. Receive message and validate non-empty input | Deterministic | Required fields and empty-input rejection are exact rules. |
| 2. Extract intent, summary, actions, evidence, and possible dates | LLM judgment | Language and implied intent vary too much for a fixed parser. Output must match a Pydantic schema. |
| 3. Ground evidence and dates in the source message | Deterministic | Unsupported quotes and dates can be detected and downgraded or removed consistently. |
| 4. Resolve supported relative dates and priority | Deterministic | Calendar arithmetic and urgency policy should not vary between runs. |
| 5. Decide whether a reply is needed | LLM judgment + deterministic policy | The model interprets intent; explicit questions and reply phrases provide a deterministic floor. |
| 6. Draft a reply when needed | LLM judgment | Tone and wording require language judgment, but the draft may use only validated facts and actions. |
| 7. Review grounding and safety | LLM judgment + deterministic policy | A second model pass finds semantic problems; code enforces non-negotiable authorization rules. |
| 8. Persist the result and audit state | Deterministic | SQLite records the message, actions, status, revisions, and decisions. |
| 9. Correct, approve, or reject | Human-in-the-loop | A person owns factual corrections and the final decision. Approval never sends the draft. |
| 10. Create an external draft or task in a future integration | Deterministic after human approval | Side effects belong behind an idempotent adapter and an approval check; they are intentionally absent from v0.1. |

The operating boundary is deliberate: the model proposes; deterministic policies constrain; a human
decides. See [`docs/WORKFLOW_AND_DEPLOYMENT.md`](docs/WORKFLOW_AND_DEPLOYMENT.md) for exceptions,
integration points, rollout stages, error handling, and the FDE audit → evals → deployment loop.

## Product goal

The assistant should be useful every day: reduce inbox review time, prevent commitments from being
missed, and prepare trustworthy replies without taking external action without approval. Success is
measured through time saved, extraction accuracy, human corrections, and recurring use—not merely by
the number of implemented features.

## Flow

```text
Message -> Analysis Agent -> optional Draft Agent -> Review Agent -> SQLite
```

```text
Existing inbox / form
        |
        v
Ingestion adapter --idempotency key--> InboxService
        |                                  |
        |                         LLM judgment + schemas
        |                                  |
        |                         deterministic policies
        |                                  |
        +----------------------------> SQLite audit record
                                           |
                                           v
                                    Human review queue
                                           |
                                  approve / revise / reject
                                           |
                                           v
                             Future side-effect adapter (gated)
```

## Installation

```bash
git clone https://github.com/pmigliasso1980/inbox-to-action-assistant.git
cd inbox-to-action-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export OPENAI_API_KEY="your-key"
```

## Process a message

```bash
python3 -m src.inbox_action ingest \
  --sender "ana@example.com" \
  --subject "Proposal and meeting" \
  "Please review the proposal by Friday and confirm whether you will attend on Monday."
```

The application tries the preferred model followed by configured fallbacks and reuses the first model
the API key can access. Results include the selected model, analysis, tasks, draft, and review.

Unambiguous relative dates are resolved from the reference date; ambiguous dates remain
`needs_confirmation`. Explicit urgency produces `urgent`, while a verified deadline today or tomorrow
produces `high`. Future commitments receive `requires_human_approval` without automatically invalidating
an otherwise sound review. Every result remains `pending_human_review`.

## Review results

```bash
python3 -m src.inbox_action list
python3 -m src.inbox_action show 1
python3 -m src.inbox_action history 1
python3 -m src.inbox_action approve 1 --note "Verified before replying"
python3 -m src.inbox_action reject 1 --note "The proposed date is incorrect"
```

To revise an analysis or draft, export the corresponding JSON object, edit it, and run:

```bash
python3 -m src.inbox_action revise 1 \
  --analysis-file analysis.json \
  --draft-file draft.json \
  --note "Corrected the owner and date"
```

Use `--clear-draft` to remove a draft. Every revision and decision is stored in `review_events` with
before-and-after snapshots. A revision returns the message to `pending_human_review`.

## Offline tests

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_evaluation_cases -v
```

The daily evaluation fixtures live in `evals/daily_cases.json`. Offline evaluation validates
deterministic policies against known structured outputs without API calls or SQLite writes.
The open-ended taxonomy, risk tiers, sampling strategy, release gates, and expansion roadmap are
documented in [`docs/EVALUATION_STRATEGY.md`](docs/EVALUATION_STRATEGY.md).

The personal capability baseline, shadow-pilot commitment, blocked time, and monthly checkpoints are
documented in [`docs/90_DAY_PLAN.md`](docs/90_DAY_PLAN.md).

The MCP paper-design lab decomposes the target inbox workflow into system-owned servers, tools,
resources, and prompts in [`docs/MCP_CAPABILITY_MAP.md`](docs/MCP_CAPABILITY_MAP.md).

The follow-on architecture and protocol-fluency lab diagrams explicit clients and transports, stress
tests failure isolation, writes JSON-RPC messages by hand, and traces a complete call in
[`docs/MCP_ARCHITECTURE_AND_WIRE.md`](docs/MCP_ARCHITECTURE_AND_WIRE.md).

The executable MCP course project starts in [`mcp-document-server/server.py`](mcp-document-server/server.py),
with reproducible setup and observed debugging evidence in
[`mcp-document-server/LAB_NOTES.md`](mcp-document-server/LAB_NOTES.md).

Its four typed tools, generated-schema checks, direct-call harness, Inspector smoke test, and observed
results are documented in
[`mcp-document-server/MODULE_4_LAB_NOTES.md`](mcp-document-server/MODULE_4_LAB_NOTES.md).

The async reference client in [`mcp-document-server/client.py`](mcp-document-server/client.py)
demonstrates initialization, discovery, typed-content extraction, both MCP failure channels, safe
subprocess cleanup, and concurrent calls.

Observed handshake, discovery, naive-client failure, content-block behavior, round-trip state, and the
five-case failure taxonomy are recorded in
[`mcp-document-server/MODULE_5_LAB_NOTES.md`](mcp-document-server/MODULE_5_LAB_NOTES.md).

## Deployment strategy

The first production integration should sit beside the company's existing inbox and task system:

1. An adapter reads a bounded mailbox or receives a webhook; the existing system remains the source.
2. `InboxService` performs judgment and policy enforcement without external side effects.
3. SQLite is suitable for the local pilot; a managed relational database replaces it for concurrent
   production use while preserving the repository boundary.
4. A review UI displays source evidence, structured actions, draft, risks, and audit history.
5. Only an approved record may reach a separate, idempotent draft/task adapter. Sending remains a
   distinct human action unless later evidence supports more autonomy.

Rollout is **sandbox → shadow mode → reviewed drafts → narrowly approved actions**. Advancement requires
the evaluation gates in `docs/EVALUATION_STRATEGY.md`; a high average score cannot offset a serious
safety failure. Integration pseudocode with explicit failure paths is in
[`examples/integration_strategy.py`](examples/integration_strategy.py).

## Error-handling policy

- Empty input fails before any model call.
- Model access denial tries the documented fallback list; other API errors propagate to the caller for
  bounded retry at the integration boundary.
- Every model response is schema-validated by Pydantic; missing structured output fails closed.
- Unsupported evidence lowers confidence; unsupported dates are removed; ambiguous dates are marked
  `needs_confirmation`.
- Missing required drafts and unsafe commitments receive risk flags and remain pending human review.
- Unknown IDs and empty revisions fail explicitly rather than silently changing state.
- Integration calls use bounded exponential backoff for transient failures, idempotency keys to prevent
  duplicates, and a dead-letter queue after retries. Validation and authorization failures are never
  retried as if they were transient.
- The current application never sends, deletes, publishes, or modifies an external system.

## Live evaluation

With `OPENAI_API_KEY` configured, evaluate the complete model workflow without persisting messages:

```bash
# Start with one case to inspect the report and control cost
python3 -m src.inbox_action eval-live --case informational_no_action

# Run all cases
python3 -m src.inbox_action eval-live
```

Repeat `--case` to select multiple scenarios. The command prints JSON with individual checks,
dimension summaries (`extraction`, `dates`, `priority`, `response`, `draft_quality`, `review`, and
`safety`), and the actual outputs. It exits with status `1` when any case fails. The full suite can make
up to 17 model calls.

Live evaluation also checks that temporal text and evidence are grounded in the original message, every
action has confidence of at least `0.7`, drafts contain no unresolved placeholders, and sensitive
external actions retain explicit human control.

## Roadmap

1. Expand regression coverage with additional anonymized everyday scenarios.
2. Measure missed actions, false positives, draft corrections, and time saved.
3. Build a daily review queue with correction, approval, and rejection controls.
4. Add a simple web interface.
5. Add read-only Gmail ingestion.
6. Create drafts and reminders only after explicit human approval.
7. Track quality, cost, latency, and recurring use.
