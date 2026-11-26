"""Propose README links to existing lab reports."""

import json
import sys
from pathlib import Path


def propose(root: Path, attempt: int) -> str:
    reports = sorted(root.glob("experiments/*/README.md"))
    if attempt > 1:
        reports += sorted(root.glob("experiments/*/RESULTS.md"))
        reports += sorted(root.glob("experiments/*/COMPARISON.md"))
    return "".join(f"- [{path.parent.name}]({path.relative_to(root).as_posix()})\n"
                   for path in sorted(reports))


if __name__ == "__main__":
    print(json.dumps(propose(Path(sys.argv[1]), int(sys.argv[2]))))
