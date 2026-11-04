# Lab 1 submission: Read Your Token Bill

This is the repository-root grading entry point for the current lab. The expanded calculations and source descriptions are in [`token-cost-lab-1/README.md`](token-cost-lab-1/README.md), and the 30-turn spreadsheet is [`token-cost-lab-1/loop-tax.csv`](token-cost-lab-1/loop-tax.csv).

Track: **Track A — Codex CLI**

Price sheet: uncached input **$2.00/M**, output **$10.00/M**, cache write **$2.50/M**, cached input **$0.20/M**.

## Exercise 1: five token predictions and counts

Actual counts use `tiktoken 0.14.0` with the `o200k_base` encoding. Predictions are characters divided by four.

| Content | Characters | Predicted | Counted | Counted/predicted |
|---|---:|---:|---:|---:|
| One-line prompt | 50 | 12.50 | 11 | 0.880 |
| English paragraph | 264 | 66.00 | 49 | 0.742 |
| Same paragraph in Spanish | 309 | 77.25 | 62 | 0.803 |
| `mcp-capstone/server.py`, 213 lines | 6,948 | 1,737.00 | 1,575 | 0.907 |
| `evals/daily_cases.json`, 205 lines | 6,563 | 1,640.75 | 1,652 | 1.007 |

The rule underestimated JSON the most: **1,652 counted versus 1,640.75 predicted**, a **1.007 ratio**.

Spanish used **13 more tokens** than English: **62 versus 49 tokens**.

## Exercise 2: price three calls

| Call | Uncached | Cache write | Cached | Output | Real context | Cost | Output share |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 12,400 | 0 | 0 | 1,850 | 12,400 | **$0.043300** | 42.73% |
| 2 | 900 | 0 | 11,500 | 1,850 | 12,400 | **$0.022600** | 81.86% |
| 3 | 900 | 11,500 | 0 | 1,850 | 12,400 | **$0.049050** | 37.72% |

The provider report `input 12,400; cached 11,500; output 1,850` normalizes to **900 uncached input, 0 cache write, 11,500 cached input, and 1,850 output**.

For 10,000 monthly calls, Call 1 costs **$433.00**, Call 2 costs **$226.00**, and the Call 2 pattern saves **$207.00/month**.

## Exercise 3: the loop tax

The complete per-turn spreadsheet has 30 rows in [`token-cost-lab-1/loop-tax.csv`](token-cost-lab-1/loop-tax.csv).

| Run | Total input | Total output | Total cost |
|---|---:|---:|---:|
| 20 turns | 445,000 | 8,000 | **$0.970** |
| 30 turns | 892,500 | 12,000 | **$1.905** |

Pasting a 5,000-token file on turn 1 of the 30-turn run adds **150,000 input tokens** and **$0.300**, raising cost to **$2.205**. The cheapest avoidance is to retrieve only the needed excerpt for the one turn and then remove or compact it; sending the 5,000 tokens once costs **$0.010**.

## Exercise 4: cost per completed task

| Setup | API spend | Tickets reaching a person | People cost | Total cost |
|---|---:|---:|---:|---:|
| A, 55% success | **$5.80** | **202.5** | $405.00 | **$410.80** |
| B, 92% success | **$11.88** | **6.4** | $12.80 | **$24.68** |

Cost per call hid failure and human-escalation cost: the higher-priced model costs **$386.12 less per 1,000 completed tickets**.

## Exercise 5: real baseline

- **Task:** Draft a concise professional email from synthetic scheduling notes in a fresh, isolated, read-only Codex CLI session.
- **Turns:** 1.
- **Context at end:** **15,048 tokens**: 14,977 input plus 71 output.
- **Biggest context item:** Codex system instructions, tool definitions, and installed skill metadata.
- **Normalized usage:** 7,553 uncached input; 0 cache write; 7,424 cached input; 71 output.
- **Cost:** **$0.017301** using the lab price sheet.
- **Completed to quality bar:** **yes**.

The output contained a subject, the changed Thursday 10:00 meeting time, the Wednesday-noon blocker deadline, and a concise thank-you. The surprising baseline finding was that a tiny email prompt still ended with **15,048 context tokens**, because fixed agent instructions and tools dominated the task content.

## Archived earlier lab notes

The previous root `LAB_NOTES.md` for the MCP client lab is preserved as [`MCP_CLIENT_LAB_NOTES.md`](MCP_CLIENT_LAB_NOTES.md).
