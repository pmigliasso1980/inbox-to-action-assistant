"""Run a bounded generator/evaluator loop against an isolated Git snapshot."""

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAX_ATTEMPTS = 2


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, timeout=15)


def invoke(role, snapshot, *args, input_text=None):
    return subprocess.run(
        [sys.executable, str(HERE / f"{role}.py"), str(snapshot), *args],
        input=input_text, capture_output=True, text=True, timeout=5,
    )


def main() -> int:
    before = git("status", "--porcelain")
    revision = git("rev-parse", "HEAD").decode().strip()
    events = []
    accepted = False
    with TemporaryDirectory(prefix="lab-index-") as directory:
        snapshot = Path(directory)
        paths = ["experiments/boundary_e2e", "experiments/wip_vcr"]
        with ZipFile(io.BytesIO(git("archive", "--format=zip", revision, *paths))) as archive:
            archive.extractall(snapshot)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            proposal = invoke("generator", snapshot, str(attempt))
            proposal.check_returncode()
            candidate = json.loads(proposal.stdout)
            review = invoke("evaluator", snapshot, input_text=proposal.stdout)
            if review.returncode not in (0, 1):
                review.check_returncode()
            verdict = json.loads(review.stdout)
            if verdict["passed"] != (review.returncode == 0):
                raise RuntimeError("Evaluator verdict disagrees with exit status")
            events.append(dict(attempt=attempt, candidate=candidate,
                               candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),
                               generator_exit=proposal.returncode, evaluator_exit=review.returncode,
                               verdict=verdict))
            if verdict["passed"]:
                accepted = True
                break
    after = git("status", "--porcelain")
    isolated = not snapshot.exists()
    result = dict(source_revision=revision, attempts=events, accepted=accepted,
                  temporary_snapshot_removed=isolated,
                  porcelain_before=before.decode(), porcelain_after=after.decode(),
                  workspace_status_unchanged=before == after,
                  next_action="Human reviews candidate before any README change" if accepted else
                  "Human investigates failed acceptance before retry",
                  paid_model_calls=0)
    print(json.dumps(result, indent=2))
    return 0 if accepted and isolated and before == after else 1


if __name__ == "__main__":
    raise SystemExit(main())
