# Lab 1: Read Your Token Bill

Track: **Track A — Codex CLI**

Price sheet used throughout: uncached input **$2.00/M**, output **$10.00/M**, cache write **$2.50/M**, and cached input **$0.20/M**.

## Exercise 1 — Predict, then count

Counts use OpenAI's `o200k_base` tokenizer through `tiktoken 0.14.0`. Predictions use `characters ÷ 4` without rounding before calculating the ratio.

| Content | Source | Characters | Predicted tokens | Counted tokens | Counted / predicted |
|---|---|---:|---:|---:|---:|
| One-line prompt | “Maybe we can re-use inbox-to-action-assistant repo” | 50 | 12.50 | 11 | 0.880 |
| English prose | Project-description paragraph reproduced below | 264 | 66.00 | 49 | 0.742 |
| Spanish prose | Translation of the same paragraph, reproduced below | 309 | 77.25 | 62 | 0.803 |
| Python source, about 200 lines | `mcp-capstone/server.py` — 213 lines | 6,948 | 1,737.00 | 1,575 | 0.907 |
| JSON of similar size | `evals/daily_cases.json` — 205 lines | 6,563 | 1,640.75 | 1,652 | 1.007 |

**English sample:** The Inbox-to-Action Assistant turns emails, messages, or notes into summaries, tasks, dates, priorities, and reviewed reply drafts. The current version accepts manually pasted text and stores results in SQLite. It never sends messages or performs external actions.

**Spanish sample:** El Asistente de Bandeja de Entrada a Acción convierte correos electrónicos, mensajes o notas en resúmenes, tareas, fechas, prioridades y borradores de respuesta revisados. La versión actual acepta texto pegado manualmente y almacena los resultados en SQLite. Nunca envía mensajes ni realiza acciones externas.

The 4-character rule underestimated the JSON most: its actual count was **1,652 tokens**, **11.25 tokens** above the unrounded prediction of **1,640.75**, for a **1.007 ratio**.

The Spanish version used **13 more tokens** than the English version (**62 versus 49**), even though the Spanish text was only **45 characters longer**.

## Exercise 2 — Price three calls

Formula:

```text
cost = (uncached × $2.00 + cache_write × $2.50
        + cached × $0.20 + output × $10.00) / 1,000,000
```

| Call | Uncached input | Cache write | Cached input | Output | Real context | Total cost | Output share of cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 12,400 | 0 | 0 | 1,850 | 12,400 | $0.043300 | 42.73% |
| 2 | 900 | 0 | 11,500 | 1,850 | 12,400 | $0.022600 | 81.86% |
| 3 | 900 | 11,500 | 0 | 1,850 | 12,400 | $0.049050 | 37.72% |

For the provider report `input 12,400; cached 11,500; output 1,850`, the normalized numbers are:

```text
uncached input = 12,400 − 11,500 = 900
cache write    = 0
cached input   = 11,500
output         = 1,850
```

At **10,000 calls/month**, Call 1 costs **$433.00/month** and Call 2 costs **$226.00/month**, so Call 2 saves **$207.00/month**.

## Exercise 3 — The loop tax

The spreadsheet is in [`loop-tax.csv`](loop-tax.csv). Turn 1 sends the 8,000-token fixed prefix; each completed turn adds 1,500 tokens to all later inputs. Each turn produces 400 output tokens.

| Run | Total input | Total output | Input cost | Output cost | Total cost |
|---|---:|---:|---:|---:|---:|
| 20 turns | 445,000 | 8,000 | $0.890 | $0.080 | **$0.970** |
| 30 turns | 892,500 | 12,000 | $1.785 | $0.120 | **$1.905** |

A 5,000-token file pasted on turn 1 remains in every input of the 30-turn run. It adds **150,000 input tokens** (`5,000 × 30`) and **$0.300**, raising total cost from **$1.905 to $2.205**.

The cheapest avoidance is to retrieve or attach only the needed excerpt for the one turn that uses it, then remove or compact it; sending 5,000 tokens once costs **$0.010**, versus **$0.300** when retained for all 30 turns.

## Exercise 4 — Cost per completed task

Expected counts are allowed to be fractional across a population of 1,000 tickets.

### Setup A — small model

- First attempts: `1,000`
- Second attempts: `1,000 × (1 − 0.55) = 450`
- API spend: `(1,000 + 450) × $0.004 = $5.80`
- Tickets reaching a person: `450 × (1 − 0.55) = 202.5`
- People cost: `202.5 × $2.00 = $405.00`
- **Total cost: $410.80**

### Setup B — larger model

- First attempts: `1,000`
- Second attempts: `1,000 × (1 − 0.92) = 80`
- API spend: `(1,000 + 80) × $0.011 = $11.88`
- Tickets reaching a person: `80 × (1 − 0.92) = 6.4`
- People cost: `6.4 × $2.00 = $12.80`
- **Total cost: $24.68**

Cost per call hid the failure and escalation cost: despite charging more per attempt, Setup B costs **$386.12 less per 1,000 completed tickets** because far fewer tickets require a person.

## Exercise 5 — Baseline of a real task

**Task:** Draft a professional email from synthetic scheduling notes in a fresh, isolated, read-only Codex CLI session.

**Turns:** 1

**Context at end:** 15,048 tokens (`14,977 input + 71 output`)

**Biggest thing in context:** Codex's system instructions, tool definitions, and installed skill metadata; the task prompt itself was short.

**Normalized usage:**

- Uncached input: `14,977 − 7,424 = 7,553`
- Cache write: `0`
- Cached input: `7,424`
- Output: `71`

**Cost:** `(7,553 × $2.00 + 7,424 × $0.20 + 71 × $10.00) / 1,000,000 = $0.017301`

**Completed to quality bar:** yes. The result contained a clear subject, the new meeting time, the blocker deadline, and an appropriate thank-you, with no unsupported additions beyond a standard sign-off placeholder.

### Baseline output

> **Subject: Project Review Rescheduled to Thursday at 10:00**
>
> Hi everyone,
>
> The project review has been moved to Thursday at 10:00. Please send any blockers by Wednesday at noon so we can address them during the review.
>
> Thank you for your flexibility and for adapting to the schedule change.
>
> Best,
>
> [Your Name]

## Reproducibility note

The raw token-count inputs, arithmetic, and exact baseline usage are preserved in this document and `loop-tax.csv`. No repository content was sent during the baseline call; only synthetic scheduling notes were used.
