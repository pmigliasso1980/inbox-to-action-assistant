# Initialization and context reset

Baseline: `7f0f1a6`. Start with [AGENTS.md](AGENTS.md) and the
[repository guide](docs/REPOSITORY_GUIDE.md).

## Startup-readiness checklist and ordered work

1. [x] Record the source revision and export a clean snapshot with `git archive`.
2. [x] Locate the stack and declared dependencies in [pyproject.toml](pyproject.toml).
3. [x] Identify the offline verification entry point and the initial focused
   check in [graph/test_repository_contracts.py](graph/test_repository_contracts.py).
4. [x] Run the full test suite and compile check on the clean snapshot.
5. [x] Record timing, environment findings, and the limits of the measurement.

Start with `python3 -m pytest -q graph/test_repository_contracts.py` for the
focused check, then run `python3 -m pytest -q` for the full suite.
No model calls are required.

## Measured reset

Timed with `/usr/bin/time -p` on macOS using Python 3.11.3. From a new
`zsh -f` process, the timer included creating a temporary directory,
exporting committed HEAD, reading the two startup files from that directory,
running the full suite, and compiling the core Python directories.
The snapshot excluded working-tree changes and untracked files.

- First attempt: **0.81 s** to failure. The existing project virtual
  environment passed `pip check` but lacked pytest.
- Second attempt: **0.58 s** to failure. The shared interpreter contained
  pytest but had a FastAPI/Starlette dependency conflict.
- Successful warm-dependency reset: **1.95 s**, with **93 tests passing**
  and a successful compile check. This used the shared interpreter.

- Isolated follow-up: **3.11 s**. A fresh virtual environment was prepared
  ahead of timing with `anthropic>=0.60`, `openai>=2.53.0`, `pydantic>=2.0`,
  and `pytest`. The same clean-snapshot procedure included `pip check`,
  which passed, followed by 93 passing tests, 2 passing subtests, and a
  successful compile check.

The 3.11-second result measures a scripted repository reset and verification
with dependencies already installed. It excludes dependency installation,
network clone time, and human or agent comprehension time. The scripted
reset met the 180-second threshold. This handoff records the two environment
failure modes so the next session can check them before rerunning the lab.
