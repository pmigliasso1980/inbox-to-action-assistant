# Lab 1.2 zero-shot baseline report

## The task is fixed, objectively scored, and useful for later grounding

The course-long task is a Python code-review assistant. Each input is a self-contained source snippet; the output is a structured list of defects with category, exact line, severity, and rationale. It is objectively evaluable because the 20-item measurement set contains seeded defects and the scorer computes exact category-and-line precision, recall, and F1. It is non-trivial because hard items contain interacting security, concurrency, and data-integrity defects. It is amenable to grounding because later modules can retrieve API contracts, security rules, call relationships, and prior findings as entities and relationships.

The frozen prompt is `evals/prompt_baseline.txt`. Dataset version `1.1.0` contains 20 measurement items: 6 easy, 10 medium, and 4 hard. Five separate development items live in `evals/devset.jsonl` and were not used to tune against measurement outputs.

## Two unchanged runs establish a 6.67-point noise floor

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Mean F1 | 0.8786 | 0.9452 |
| Input tokens | 19,012 | 19,012 |
| Output tokens | 1,960 | 1,981 |
| Cost | $0.144060 | $0.144585 |
| Mean latency/item | 2.778 s | 3.574 s |
| Wall-clock time | 55.586 s | 71.500 s |

The absolute score difference is **0.0667**, or **6.67 percentage points**. A later architecture change must improve by materially more than 6.67 points before one two-run comparison is persuasive. The two official runs used 38,024 input tokens, 3,941 output tokens, cost **$0.288645**, and averaged **3.176 seconds/item**.

No model judge was used. Scoring is deterministic, so a judge-agreement audit is not applicable.

## A calibration failure was preserved instead of hidden

Before the official baseline, dataset version `1.0.0` produced misleading scores of 0.325 and 0.345. The model often found the correct defect but used a synonym such as `mutable_default_argument`, while the scorer expected `mutable_default`; one snippet also contained accidental unlabelled defects. Those 40 calls are retained under `runs/calibration-taxonomy-v1/` and are not reported as the baseline. The measurement instrument was corrected once, versioned to `1.1.0`, and then frozen before the two official runs. This was an evaluation-harness correction, not prompt tuning for higher task performance.

## The five worst failure patterns define the architectural roadmap

1. **Item 012 — unstable line attribution (Run 1: 0.000; Run 2: 1.000).** Both runs found the race condition, but Run 1 placed it on the read and Run 2 on the write. The output was structurally close but inconsistent on evidence location; a reflection pass in **Module 2** should re-check each cited line against its rationale.
2. **Item 017 — multi-defect download helper (both runs: 0.571).** The model found SSRF and missing timeout but placed `unchecked_status` on the request rather than the write and added an unlabelled path-traversal concern. The model tried to do several checks at once and lost scoring coherence; planning/chaining in **Modules 4 and 6** should separate network, response, and filesystem review passes.
3. **Item 006 — speculative timeout finding (Run 1: 0.667; Run 2: 1.000).** Run 1 correctly found the missing `await` but assumed a timeout contract not established by the snippet. Reflection in **Module 2** should require every reported finding to cite code-supported evidence and reject speculative extras.
4. **Item 011 — extra unchecked-status finding (both runs: 0.667).** Both runs found command injection and then reported a second concern outside the seeded list. A second reviewer with a precision-focused role in **Module 5** can challenge whether each extra is in scope and materially actionable.
5. **Item 018 — missed shared-cache race (both runs: 0.667).** Both runs found the incorrect cache key but missed unsynchronized shared mutation. A concurrency-specialist reviewer in **Module 5**, supported later by graph knowledge about shared state in **Module 8**, should target this blind spot.

## The baseline is the number to beat, not a claim of general code-review quality

The official baseline is reported as the pair **0.8786 and 0.9452**, not their average alone. Raw model outputs, deterministic score details, latency, usage, and cost for every item are stored under `runs/baseline/run-1/` and `runs/baseline/run-2/`. Future modules must preserve dataset version `1.1.0`, the frozen prompt, and the scorer or explicitly version and rerun the baseline.
