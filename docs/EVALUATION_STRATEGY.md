# Evaluation Strategy

## Purpose

The evaluation system exists to answer a product question: can people trust the assistant to identify
what matters, avoid inventing work, prepare useful drafts, and preserve human control during everyday
inbox use?

The space of possible messages is effectively unlimited. The suite therefore must not become a flat,
ever-growing list of topics. It should cover a finite set of behavioral dimensions, combine them
systematically, and add regression cases whenever real failures reveal a new boundary.

## Core principles

1. Evaluate behaviors and risks, not just message topics.
2. Keep deterministic policy tests separate from variable live-model evaluations.
3. Measure dimensions independently so one success cannot hide another failure.
4. Prefer small, diagnostic cases before long realistic conversations.
5. Add every confirmed production failure as a permanent regression case.
6. Use pairwise and risk-based combinations instead of attempting the full Cartesian product.
7. Never improve scores by weakening a safety requirement or making a criterion meaningless.
8. Keep all fixtures synthetic or anonymized; never commit private inbox content.

## Evaluation layers

### Layer 1: unit policy tests

Fast, deterministic, and free of API calls. These prove date parsing, evidence grounding, priority
rules, state transitions, and safety overrides.

Run on every change. A failure blocks merging.

### Layer 2: structured regression fixtures

Known model-shaped inputs are passed through deterministic policies. These verify complete scenarios
without model variance and make failures easy to diagnose.

Run on every change. A failure blocks merging.

### Layer 3: live single-run evaluation

The real Analysis, Draft, and Review agents process the scenario suite. Results are reported by
dimension. This detects prompt weaknesses and model variance.

Run for prompt, schema, policy, model, or evaluation changes. A safety failure blocks release. Other
failures create a triage item.

### Layer 4: repeated live evaluation

High-risk and historically unstable cases run multiple times. This measures consistency rather than a
single lucky output.

Run before a release candidate and after model or prompt changes.

### Layer 5: shadow evaluation with anonymized messages

Realistic messages are processed without sending replies or creating external actions. Human reviewers
label omissions, false positives, usefulness, and required edits.

Run before enabling a new integration or automation level.

## Open-ended taxonomy

Each case should be tagged across the following independent axes. New categories extend an axis or add a
new one; they do not require redesigning the whole suite.

### 1. Message intent

- purely informational
- explicit request
- implicit request
- question requiring an answer
- approval request
- status update
- reminder or follow-up
- delegation
- cancellation
- reschedule
- correction or changed instructions
- escalation or complaint
- acknowledgment or thanks
- marketing, newsletter, or spam

### 2. Action structure

- no action
- one action
- multiple independent actions
- ordered dependent actions
- conditional action
- recurring action
- optional action
- action assigned to the user
- action assigned to another person
- shared ownership
- missing owner
- conflicting owners

### 3. Time semantics

- no date
- absolute date
- relative day
- weekday crossing a week boundary
- time of day
- timezone conversion
- date range
- multiple alternative dates
- vague deadline
- recurring schedule
- deadline changed later in a thread
- past date
- impossible date
- locale-sensitive date
- daylight-saving boundary

### 4. Priority and urgency

- no urgency
- explicit urgency
- near verified deadline
- important but not urgent
- urgency without an action
- false urgency or marketing pressure
- conflicting urgency signals
- emergency language requiring human escalation

### 5. Conversation structure

- standalone message
- quoted history
- reply with missing context
- multi-turn thread
- multiple senders
- forwarded message
- request changed in a later message
- action completed in a later message
- duplicate message
- repeated reminder
- contradictory instructions

### 6. Draft behavior

- no reply needed
- acknowledgment only
- answer known from the message
- answer requires verification
- clarification question
- tentative commitment
- rejection or boundary setting
- rescheduling proposal
- multiple questions answered
- tone adaptation
- unknown identity or signature
- attachment referenced but unavailable

### 7. Safety and authorization

- harmless local task
- external side effect
- sending or publishing
- deleting or modifying data
- financial commitment
- legal or contractual statement
- credential or secret request
- personal or sensitive information
- medical or safety-critical content
- suspicious link or social engineering
- instruction injection inside message content
- request to bypass approval
- urgent external action without authorization

### 8. Grounding and hallucination risk

- unsupported date
- unsupported owner
- unsupported completed action
- unsupported receipt or availability
- extra task not requested
- missing task
- evidence paraphrased instead of quoted
- quote with harmless punctuation changes
- conflicting evidence
- attachment contents assumed without access

### 9. Language and format

- English
- Spanish
- mixed-language message
- code switching
- formal and informal tone
- typos and missing accents
- short fragment
- long prose
- bullet list
- table-like text
- HTML residue
- signatures and disclaimers
- emoji and shorthand

### 10. Adversarial and noisy input

- empty or whitespace-only input
- extremely long input
- repeated text
- malformed dates
- quoted prompt injection
- fake system instructions
- hidden instructions in a signature
- irrelevant legal disclaimer
- tracking links
- corrupted encoding

## Risk tiers

### Tier 0: harmless classification

Examples: newsletters, FYI messages, simple filing tasks. False positives are inconvenient but
recoverable.

### Tier 1: communication risk

Examples: ordinary reply drafts, scheduling, commitments, and ownership. Errors can create confusion or
missed work.

### Tier 2: operational risk

Examples: service restarts, publishing, modifying records, or contacting third parties. Explicit human
approval is mandatory.

### Tier 3: high-impact risk

Examples: financial, legal, medical, credential, deletion, or sensitive-data actions. The assistant
should default to escalation, minimal claims, and no external action.

Coverage targets and repetition counts increase with risk tier.

## Case schema evolution

Extend each fixture with metadata while keeping the current fields backward compatible:

```json
{
  "name": "stable_machine_name",
  "description": "Human-readable behavior being tested",
  "tags": ["intent:request", "time:none", "risk:tier1", "language:en"],
  "risk_tier": 1,
  "source": "synthetic",
  "current_date": "2026-08-06",
  "timezone": "America/Argentina/Cordoba",
  "sender": "sender@example.com",
  "subject": "Human subject",
  "body": "Synthetic or anonymized content",
  "expected": {},
  "live_expected": {},
  "invariants": [],
  "allowed_variants": {},
  "repeat_count": 1
}
```

Important distinctions:

- `expected` describes deterministic fixture behavior.
- `live_expected` describes model behavior that must be stable.
- `invariants` describe conditions that must always hold, especially safety and grounding.
- `allowed_variants` records genuinely acceptable alternatives without disabling the entire check.

## Dimensions and metrics

Continue reporting current dimensions and add metrics gradually:

- extraction: action precision, recall, owners, evidence, confidence
- dates: resolution accuracy, grounding, ambiguity handling
- priority: supported urgency and deadline-based ranking
- response: required, optional, or unnecessary reply
- draft quality: completeness, concision, tone, placeholders, unsupported additions
- review: agreement with labeled safe/unsafe behavior and consistency with its own notes
- safety: false approvals, missing authorization, secret requests, unsafe recommendations
- persistence: correct message, action, revision, decision, and audit state
- performance: latency and model-call count
- cost: tokens and estimated cost per message and per suite

Safety metrics must be reported separately from the overall average. A high average cannot compensate for
a false approval in a high-risk case.

## Sampling strategy for unlimited combinations

Use four complementary pools:

1. **Core smoke set:** one canonical case for every major axis value. Small and run frequently.
2. **Pairwise matrix:** generated or selected cases covering pairs such as ambiguous date + multiple
   owners, urgent + external action, or mixed language + changed instructions.
3. **Risk set:** dense coverage and repeated runs for Tier 2 and Tier 3 behavior.
4. **Regression archive:** every confirmed real failure, permanently retained and tagged.

Do not generate the full Cartesian product. Use pairwise coverage for ordinary behavior and targeted
three-way combinations only when risk analysis or observed failures justify them.

## Case admission rules

A new case must have:

- one primary behavior under test
- explicit tags and risk tier
- a clear expected outcome or invariant
- synthetic or anonymized content
- an explanation of why an existing case does not cover it
- a deterministic regression when the failure can be enforced by policy
- a live criterion only when model behavior matters

Cases should not be added merely because wording differs. Add them when wording exposes a meaningful
language, format, grounding, or behavioral boundary.

## Failure triage

Classify every live failure before changing code:

1. fixture error
2. evaluator false positive or false negative
3. deterministic policy gap
4. analysis prompt failure
5. draft prompt failure
6. review prompt failure
7. model variance
8. product ambiguity requiring a decision

The fix must target the correct layer. Never alter expectations solely to turn a red result green.

## Stability and release gates

### Pull-request gate

- all unit and structured regression tests pass
- no new safety failure
- every changed behavior has a regression test

### Baseline gate

- two consecutive full live runs without Tier 2 or Tier 3 safety failures
- at least 95% pass rate on Tier 0 and Tier 1 required criteria
- no ungrounded date, owner, completed action, or evidence quote
- no unresolved placeholders

### Integration gate

Before read-only Gmail ingestion:

- at least 30 curated cases
- all ten axes represented
- at least five multi-turn or quoted-history cases
- at least five multilingual or noisy-format cases
- repeated live runs for all Tier 2 cases

Before creating Gmail drafts:

- at least 60 curated cases
- no false approval in Tier 2 or Tier 3 across repeated runs
- human reviewers accept or lightly edit at least 80% of safe drafts
- every generated draft remains user-reviewed before creation or sending

## Phased expansion roadmap

### Phase A: broaden basic inbox coverage (7 -> 20 cases)

Add cancellations, reschedules, reminders, changed deadlines, conditional requests, acknowledgments,
spam, attachments without contents, and mixed informational/action messages.

Exit when all cases pass offline and two live runs reveal no safety regression.

### Phase B: threads and state changes (20 -> 35 cases)

Add quoted history, multiple senders, duplicate requests, corrected instructions, completed actions, and
conflicting messages.

This phase may require a thread-aware input model rather than prompt changes alone.

### Phase C: multilingual and noisy input (35 -> 50 cases)

Add English, Spanish, mixed language, typos, shorthand, HTML residue, signatures, long disclaimers, and
structured lists.

### Phase D: high-risk and adversarial behavior (50 -> 70 cases)

Add external actions, deletion, money, contracts, secrets, prompt injection, sensitive data, and requests
to bypass approval. Repeat these cases multiple times.

### Phase E: shadow product evaluation

Use anonymized real messages with human labels. Measure action recall, false positives, correction rate,
draft acceptance, time saved, latency, and cost. Feed confirmed failures back into the regression archive.

## Immediate next batch

The next 13 cases should bring the suite from 7 to 20:

1. cancellation with an obsolete prior task
2. meeting reschedule with old and new dates
3. reminder that duplicates an existing action
4. changed deadline in the same message
5. conditional request: act only if approval arrives
6. explicit acknowledgment with no commitment
7. mixed FYI plus one real action
8. attachment referenced but unavailable
9. newsletter or marketing message with urgency language
10. Spanish request without accents or punctuation
11. mixed English-Spanish request
12. quoted instructions that should not become new actions
13. prompt injection embedded in message content

Implement these in small batches of three to five. Run offline tests after every batch and a full live
evaluation after each completed risk or behavior cluster.

## Maintenance cadence

- every code change: unit and structured regression suites
- every prompt or policy change: affected live cases, then full live suite
- weekly during active development: repeated high-risk set
- before integration milestones: full repeated suite and manual review
- after every confirmed real failure: anonymize, classify, add regression, then fix

The suite is healthy when it grows because it captures new behavioral boundaries—not because it stores
every message ever seen.
