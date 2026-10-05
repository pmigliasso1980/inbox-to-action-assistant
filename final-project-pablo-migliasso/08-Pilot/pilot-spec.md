# Pilot specification: referral-intake extraction assistant

## Decision and owner

- Verdict: **AUGMENT**; do not auto-write to Caregate or auto-route patients.
- Proposed client owner: Practice Operations referral-intake director.
- Proposed technical owner: Kestrel integration lead.
- Proposed risk owners: Privacy officer and Information Security lead.
- Proposed decision date: 2026-10-16.

## Before and after workflow

### Before

1. RightFax receives a referral.
2. A coordinator opens and interprets the document.
3. The coordinator uses an approximately 900-row spreadsheet to find provider/routing context.
4. The coordinator enters data into Caregate.
5. The coordinator seeks missing information and chooses the destination.

### After

1. RightFax provides a document copy to an approved, audited intake service.
2. Deterministic checks validate file type, legibility, duplicates, malware status, and required consent metadata.
3. The model proposes structured fields with field-level confidence and evidence spans.
4. Rules route every low-confidence, incomplete, handwritten, or contradictory case to human review.
5. A coordinator verifies every critical field and makes the final routing decision.
6. The system records input hash, model/version, prompt/version, proposed values, evidence, reviewer edits, timestamps, and final disposition.

## A non-AI improvement comes first

Move the provider lookup spreadsheet into a governed, versioned shared table with a named owner, change history, validation, and a standard referral cover sheet. This removes a single-person dependency and gives the model and people the same reference data. No time saving is claimed because lookup frequency was not measured.

## Scope boundaries protect patients and the organization

In scope: typed PDF/image referrals, field extraction, completeness checks, duplicate detection, evidence highlighting, and reviewer queues. Out of scope: Caregate writes, urgency diagnosis, clinical interpretation, patient routing decisions, outreach, handwritten-document automation, payer-portal actions, and use of general consumer AI accounts.

## Baseline and metrics

- Current fax volume: 3,596 referrals/month (projected from 5,800 reported referrals × 62% reported fax share).
- Current handling time: 6.3–8.1 minutes/fax (projected from a 10-case observed sample).
- Baseline replacement: collect a 2-week measured sample before release, stratified by clean, incomplete, handwritten, and duplicate cases.
- Primary metric: median verified handling time per fax. Proposed success: at least 30% lower after 400 production cases or 6 weeks.
- Quality metric: critical-field precision. Proposed minimum: 99.5% on the frozen golden set and production sample.
- Safety metric: human-review routing recall. Proposed minimum: 98% for cases requiring review.
- Operational metric: reviewer override rate, reported by field and document type; no target until the first 200 cases establish a baseline.

## Access and controls

Use synthetic and de-identified documents until Privacy, Security, and Legal approve the data path and a BAA-covered environment. Use least-privilege service identities, encryption in transit and at rest, field-level audit records, documented retention, and no model training on Kestrel data. The first release is read-only and has an immediate disable switch. A weekly reviewer panel inspects false negatives, overrides, and drift.

## Comparison method and weakness

Run a staged shadow comparison: coordinators process the normal queue while the assistant independently proposes fields, followed by a crossover phase in which reviewers use the proposals. Compare stratified median handling time and field accuracy. The method reduces patient risk but is vulnerable to learning effects and case-mix differences; randomize cases when operationally feasible and report strata separately.

## Golden set and evaluation

The repository contains 18 synthetic cases covering typical variation, exception paths, known failure modes, and adversarial instructions. Deterministic tests validate schema, required fields, expected review routing, and disallowed auto-route behavior. A human rubric evaluates semantic extraction and evidence grounding. Production sampling reviews the first 100 cases, then 10% weekly for 6 weeks, then a risk-adjusted rate approved by the owner.

### Three-level evaluation plan

- **Continuous integration assertions:** valid output schema, allowed values, required evidence spans, missing critical fields forcing `needs_human_review=true`, adversarial text never changing policy, and zero auto-route actions. A failure blocks the build.
- **Human or model-assisted judge:** compare extracted meaning and cited evidence with the labeled golden set for semantic equivalence, with a coordinator adjudicating every disagreement. Aggregate scores never override critical-field errors.
- **Production sampling:** the referral-intake owner receives a weekly quality report; Privacy and Information Security receive an immediate alert for any unapproved disclosure; the coordinator lead receives same-day alerts for misroutes, confidence drift, or override spikes.

## Rollout gates

1. Offline only: synthetic/de-identified golden-set evaluation.
2. Shadow mode: approved historical documents; no coordinator-facing output.
3. Assisted mode: a limited queue with mandatory verification.
4. Expanded assisted mode: only after the owner signs the evaluation report.

## Kill criteria

- Stop immediately for any unapproved PHI transmission or cross-tenant exposure (proposed threshold: zero incidents).
- Do not release if critical-field precision is below 99.5% after at least 200 labeled cases (proposed gate).
- Do not release if human-review routing recall is below 98% on the frozen golden set (proposed gate).
- Stop expansion if 2 patient misroutes are attributable to assistant output in any rolling 30-day period (proposed threshold).
- End or redesign the pilot if verified median handling time is not at least 30% lower after 400 production cases or 6 weeks (proposed value gate).
