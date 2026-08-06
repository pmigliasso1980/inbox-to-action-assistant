# Inbox-to-Action Assistant

Turn emails, messages, or notes into summaries, tasks, dates, priorities, and reviewed reply drafts.
The current version accepts manually pasted text and stores results in SQLite. It never sends messages
or performs external actions.

## Product goal

The assistant should be useful every day: reduce inbox review time, prevent commitments from being
missed, and prepare trustworthy replies without taking external action without approval. Success is
measured through time saved, extraction accuracy, human corrections, and recurring use—not merely by
the number of implemented features.

## Flow

```text
Message -> Analysis Agent -> optional Draft Agent -> Review Agent -> SQLite
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
