"""Independent black-box check driven by the public sprint contract."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    ("immediate", 0, 1000),
    ("one_minute", 1, 1060),
    ("five_minutes", 5, 1300),
]


def main() -> int:
    failures = 0
    for name, minutes, expected in CASES:
        request = {"delay_minutes": minutes, "now_epoch_seconds": 1000}
        process = subprocess.run(
            [sys.executable, "-m", "experiments.boundary_e2e.app"],
            input=json.dumps(request), capture_output=True, text=True,
            cwd=ROOT, timeout=5,
        )
        actual = json.loads(process.stdout) if process.returncode == 0 else None
        passed = actual == {"due_at_epoch_seconds": expected}
        failures += not passed
        print(json.dumps({"case": name, "request": request, "expected": expected,
                          "observed": actual, "app_exit_code": process.returncode,
                          "passed": passed}), flush=True)
    print(f"Contract checks: {len(CASES) - failures}/{len(CASES)} passed")
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
