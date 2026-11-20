# Fresh Session Test Scorecard

Before snapshot: commit `2c3ce3f`. A fresh reader starts with only `README.md` and `AGENTS.md`; direct answers or answers reachable through an explicit topic link are **Confident**, answers requiring repository inference are **Infer**, and absent/conflicting answers are **Unknown**.

| Question | Before | Before evidence | After | After evidence |
|---|---|---|---|---|
| What is this repository now? | Infer | README mixed product, course, and current lab narratives. | Confident | `docs/REPOSITORY_GUIDE.md` |
| How do I install it? | Confident | AGENTS.md contained explicit setup commands. | Confident | `AGENTS.md` |
| What is the full verification command? | Confident | AGENTS.md named pytest, compileall, and diff checks. | Confident | `AGENTS.md` |
| Which graph backend is local versus production? | Confident | AGENTS.md stated SQLite and PostgreSQL roles. | Confident | `graph/README.md` |
| What provenance must every claim carry? | Confident | The rule was present in AGENTS.md. | Confident | `graph/README.md` |
| Is planning in the current default path? | Unknown | ADR-003 existed but was not linked from either entry point. | Confident | `docs/DECISIONS.md` |
| Where should large artifact bodies live? | Unknown | The Rule 5 result was buried in a module report. | Confident | `docs/REPOSITORY_GUIDE.md` |
| Which source wins when documents disagree? | Unknown | No authority order existed. | Confident | `docs/REPOSITORY_GUIDE.md` |
| How are readiness reports regenerated? | Confident | AGENTS.md listed the generator commands. | Confident | `reports/README.md` |
| How do I run the incident capstone? | Confident | README linked its entry point. | Confident | `docs/REPOSITORY_GUIDE.md` |
| Where is the harness ablation evidence? | Confident | README linked the diagnostic log. | Confident | `AGENTS.md` |
| May an agent make paid model calls by default? | Confident | AGENTS.md required explicit authorization. | Confident | `AGENTS.md` |

## Totals

| Snapshot | Confident | Infer | Unknown |
|---|---:|---:|---:|
| Before `2c3ce3f` | 8 | 1 | 3 |
| After | 12 | 0 | 0 |

Confident answers increased by **4** (8/12 → 12/12). The test measures knowledge discoverability, not software quality.
