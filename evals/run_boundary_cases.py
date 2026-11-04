"""Generate the four mandatory permission-boundary observations without API calls."""
from __future__ import annotations

import json
from pathlib import Path

from agents.review_tools import ROOT, ToolError
from agents.tool_controls import ReadOnlyReviewStore, ReviewCommentBoundary, WritableCommentStore, gate_for


def main() -> None:
    out = ROOT / "runs"; audit = out / "audit.jsonl"; comments = out / "comments.jsonl"
    audit.unlink(missing_ok=True); comments.unlink(missing_ok=True)
    read = ReadOnlyReviewStore(); write = WritableCommentStore(comments)
    cases = []
    def run(name, mode, **kwargs):
        boundary = ReviewCommentBoundary(read_store=read, write_store=write, audit_path=audit, gate=gate_for(mode))
        try:
            result = boundary.post_review_comment(run_id="boundary-proof", item_id=name, **kwargs)
            cases.append({"case": name, "result": result})
        except ToolError as exc:
            cases.append({"case": name, "error": str(exc)})
    valid = {"file": "range_total.py", "line": 3, "severity": "major", "body": "range(n + 1) reads one item beyond the requested prefix."}
    run("normal-auto-approve", "auto_approve", **valid)
    run("same-auto-deny", "auto_deny", **valid)
    run("invalid-severity", "auto_approve", **{**valid, "severity": "critical"})
    run("path-traversal", "auto_approve", **{**valid, "file": "../../etc/passwd"})
    (out / "boundary-cases.json").write_text(json.dumps(cases, indent=2) + "\n")
    print(json.dumps(cases, indent=2))


if __name__ == "__main__":
    main()
