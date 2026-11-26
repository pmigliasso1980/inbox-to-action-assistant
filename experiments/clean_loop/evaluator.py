"""Verify a candidate index using a separately maintained acceptance manifest."""

import json
import re
import sys
from pathlib import Path

MANIFEST = Path(__file__).with_name("required_links.json")


def evaluate(root: Path, candidate: str) -> dict:
    expected = set(json.loads(MANIFEST.read_text()))
    paths = re.findall(r"^- \[[^\]]+\]\(([^)]+)\)$", candidate, re.MULTILINE)
    actual = set(paths)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    broken = sorted(path for path in actual & expected if not (root / path).is_file())
    malformed = len(candidate.splitlines()) - len(paths)
    duplicates = len(paths) - len(actual)
    return dict(passed=not (missing or unexpected or broken or malformed or duplicates),
                missing=missing, unexpected=unexpected, broken=broken,
                malformed=malformed, duplicates=duplicates, checked=len(paths))


if __name__ == "__main__":
    verdict = evaluate(Path(sys.argv[1]), json.load(sys.stdin))
    print(json.dumps(verdict))
    raise SystemExit(0 if verdict["passed"] else 1)
