# Module 9 Practice — 90-Day Plan

This baseline is provisional where personal or workplace evidence was unavailable.

## Honest baseline

Scale: 1 = never, 2 = tried, 3 = sometimes, 4 = reliably, 5 = could teach.

| Capability | Score | Evidence |
|---|---:|---|
| My work is findable by someone who does not know me | 4 | Public repositories contain clear READMEs, tests, architecture, and evaluation documentation. |
| I write useful closing comments | 2 | Commit messages exist, but consistent ticket-closing comments are not demonstrated. |
| I create tickets for work I identify | 2 | Proactive improvements are evident, but ticket creation is not documented. |
| I send written updates outside my immediate team | 1 | No evidence provided. |
| I maintain a project context file | 2 | Project documentation exists, but no dedicated persistent agent-context file is evident. |
| I explore and plan before implementing | 4 | Workflow, deployment, evaluation, and policy decisions are documented before expansion. |
| I verify generated code systematically | 4 | The repository has deterministic policies, automated tests, schema validation, and safety gates. |
| I have shipped a feature that calls a model | 4 | The inbox assistant uses model calls with structured outputs, fallback models, review, and persistence. |
| I describe work at user and business level | 4 | The README connects implementation to review time, missed commitments, risk, and human control. |
| I know the numbers my product area is judged on | 3 | Relevant measures are defined, but production baselines have not been collected. |
| I know what my client manager considers a good quarter | 1 | Not demonstrated; this requires a direct conversation. |
| I flag risks early in writing | 3 | Risks and failure modes are documented, but recurring stakeholder updates are not demonstrated. |
| I resolve unspecified decisions and report them | 4 | The project records explicit choices about autonomy, policies, deployment, and scope. |
| I own something nobody assigned to me | 4 | The inbox assistant and its FDE case-study materials demonstrate self-directed ownership. |
| My glue work is recorded | 3 | Reusable documentation exists, but routine collaboration and unblocking are not consistently recorded. |

**Blocking gap:** written visibility outside the immediate technical work.

**Strongest capability:** designing and verifying bounded AI workflows with structured outputs,
deterministic controls, evaluation, and human approval.

## Access checklist

These items require personal verification.

| Item | Status |
|---|---|
| Client-licensed AI assistant | Need to confirm |
| Taller Academy | Need to confirm |
| Engagement policy for tools, codebases, and data | Need to confirm with lead/security owner |
| Available certifications and access process | Need to ask the Academy contact |

Messages to send:

> Could you confirm which AI assistant I can use, which codebases and data are permitted, and where
> the current engagement policy is documented?

> Could you confirm my Taller Academy access and which AI/FDE certifications are currently available?

## Ninety-day plan

### One habit

Every Friday at 4:00 p.m., send a five-minute written update containing:

- Moved
- Helped
- Watching
- Learned

**Who sees it:** tech lead or Taller point of contact  
**Starting:** Friday, September 25, 2026

### One capability

Run the inbox assistant as a measured shadow-mode pilot using at least 20 synthetic or properly
anonymized representative messages.

Success is externally checkable when:

- The evaluation dataset contains normal, edge, ambiguous, and high-risk cases.
- Results report pass rates by evaluation dimension.
- Safety failures are reported separately.
- Correction rate, latency, model cost per message, and failure categories are measured.
- At least one deliberately induced failure demonstrates the documented fallback or human-review path.
- The results support a written ship, redesign, or stop decision.

**Deadline:** December 19, 2026  
**Blocked time:** Tuesdays, 9:00–11:00 a.m.

### One artifact

A versioned shadow-pilot evaluation report, anonymized dataset, and reproducible command stored in this
repository. No private inbox content will be committed.

### Monthly checkpoints

Schedule 15 minutes on:

- October 5, 2026
- November 2, 2026
- December 7, 2026

At each checkpoint ask:

1. Did the weekly update happen?
2. Is the shadow pilot on schedule?
3. What evidence exists?
4. If it is slipping repeatedly, what will be cut?

## Commitment to send

> **Habit:** Starting September 25, I will send you a four-section written update every Friday at
> 4:00 p.m.  
> **Capability:** By December 19, I will complete a measured shadow-mode pilot of the inbox assistant
> using at least 20 representative cases.  
> **Artifact:** I will publish a reproducible evaluation report, anonymized dataset, failure analysis,
> cost measurement, and ship/redesign/stop recommendation.

The plan is not fully committed until the access items are confirmed, the recurring blocks and
checkpoints are placed on the calendar, and the three lines above are sent to a named person.
