# Lab 3.1 report — grounded tool use

## Result

The hand-written loop in `agents/tool_agent.py` uses tools during **evaluation** (ordering B). The generator remains the frozen baseline, while the evaluator verifies the draft against canonical source and static evidence. This keeps the comparison interpretable. Measurement shows that grounding alone did not improve this already-saturated benchmark.

| Stage | Mean F1 | Delta vs baseline run 1 | Cost |
|---|---:|---:|---:|
| Baseline run 1 | 0.8786 | — | $0.144060 |
| Reflection | 0.9452 | +0.0667 | $0.351780 |
| Tools in evaluation | 0.8833 | +0.0048 | $0.669085 |

The unchanged-run noise floor is **0.0667**. Tool use improved only 0.0048 over baseline and fell 0.0619 below reflection, so it demonstrated no reliable lift. Its cost per F1 percentage point over baseline was **$1.4051**, versus **$0.0528** for reflection. Reflection was the better investment.

## Control-flow and tool evidence

Every item called `read_code` and `run_linter`: 40 total calls, mean 2.0/item. Mean latency was 5.658 seconds/item. The run used 111,557 input and 4,452 output tokens. No item hit the eight-step cap; no executor error occurred. The natural-run confirmation rejection rate was 0%. This is not evidence that confirmation is unnecessary: injected empty and garbage results were rejected in Lab 3.2. A garbage `run_tests` result with an empty observations list was rejected as `static smoke returned no relevant observations`; incorporating it would have treated unrelated output as test evidence.

The loop appends full assistant content, returns all tool results in one user message, handles `pause_turn`, emits explicit error results, performs cap synthesis, and logs arguments, summaries, confirmation verdicts, latency, and cumulative usage. `runs/tools/item-001/trace.jsonl` is a complete readable trace with parallel calls.

## Failure mapping

| Item | Prediction | Outcome and evidence |
|---|---|---|
| 012 | Source grounding might stabilize line attribution | **Not fixed.** `read_code` returned all seven lines, but the model still cited line 5 rather than the scored write on line 6. Evidence was interpreted incorrectly. |
| 017 | Static evidence might separate interacting defects | **Regressed**, 0.5714 → 0.3333. The linter found missing timeout but could not identify SSRF or locate unchecked status at line 6. The tool was too narrow. |
| 006 | Evidence checks might remove the speculative extra | **Not fixed**, remaining 0.6667. The analyzer had no async-call contract check. |
| 011 | Static evidence might eliminate the speculative extra | **Fixed**, 0.6667 → 1.000. `shell_execution` at line 4 anchored command injection without the extra finding. |
| 018 | Shared-state analysis might reveal the cache race | **Not fixed**, remaining 0.6667. The general linter returned no concurrency finding. |

The model called the intended tools on every item, so there was no “tool available but not called” case and no honest description-fix rerun to perform. The failure was capability and interpretation, not call description. The next investment should be targeted contract checks for async APIs, shared mutation, and HTTP response lifecycles—not more calls to the same general linter.
