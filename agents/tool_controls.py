"""Failure injection, explicit fallback, and local write-permission boundary."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from agents.review_tools import ROOT, ToolError, confirm_result, run_linter, run_tests

FailureMode = Literal["none", "rate_limit", "timeout", "auth", "empty", "garbage"]
GateMode = Literal["auto_approve", "auto_deny", "interactive"]

WRITE_TOOL = {
    "name": "post_review_comment",
    "description": "Post one reviewed comment to the local simulated code host only after user approval. Do not call for speculative findings or when the user has not requested a write.",
    "strict": True,
    "input_schema": {"type": "object", "properties": {
        "file": {"type": "string", "description": "Canonical benchmark filename; traversal is rejected by the executor."},
        "line": {"type": "integer", "minimum": 1, "description": "Positive source line for the comment."},
        "severity": {"type": "string", "enum": ["blocking", "major", "minor"], "description": "Fixed review severity."},
        "body": {"type": "string", "minLength": 1, "maxLength": 500, "description": "Grounded review comment body."},
    }, "required": ["file", "line", "severity", "body"], "additionalProperties": False},
}


def injected_run_tests(*, mode: FailureMode, file: str, suite: str) -> dict[str, Any]:
    if mode == "rate_limit":
        raise ToolError("rate limit exceeded, retry after 60s", retryable=True)
    if mode == "timeout":
        raise ToolError("upstream timed out after 30s", retryable=True)
    if mode == "auth":
        raise ToolError("401 unauthorized", retryable=False)
    if mode == "empty":
        return {}
    if mode == "garbage":
        return {"file": file, "suite": suite, "exit_code": 0, "stdout": "unrelated content", "stderr": "", "observations": []}
    return run_tests(file=file, suite=suite)


def explicit_test_with_fallback(*, mode: FailureMode, file: str, suite: str = "static_smoke",
                                sleep: Callable[[float], None] = lambda _: None) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, 3):
        try:
            result = injected_run_tests(mode=mode, file=file, suite=suite)
            ok, verdict = confirm_result("run_tests", result)
            attempts.append({"tool": "run_tests", "attempt": attempt, "confirmed": ok, "verdict": verdict})
            if ok:
                return {"grounded": True, "used_fallback": False, "result": result, "attempts": attempts}
            break
        except ToolError as exc:
            attempts.append({"tool": "run_tests", "attempt": attempt, "error": str(exc), "retryable": exc.retryable})
            if not exc.retryable:
                break
            if attempt < 2:
                sleep(0.01)
    fallback = run_linter(file=file, profile="all")
    ok, verdict = confirm_result("run_linter", fallback)
    attempts.append({"tool": "run_linter", "attempt": 1, "confirmed": ok, "verdict": verdict})
    return {"grounded": ok, "used_fallback": True, "result": fallback if ok else None,
            "failure": None if ok else "fallback failed; answer must be labelled ungrounded", "attempts": attempts}


@dataclass(frozen=True)
class ReadOnlyReviewStore:
    """A handle with no write method by construction."""
    project_root: Path = ROOT

    def file_exists(self, file: str) -> bool:
        from agents.review_tools import FILES
        return file in FILES


@dataclass
class WritableCommentStore:
    path: Path

    def append(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")


class ReviewCommentBoundary:
    SEVERITIES = {"blocking", "major", "minor"}

    def __init__(self, *, read_store: ReadOnlyReviewStore, write_store: WritableCommentStore,
                 audit_path: Path, gate: Callable[[dict[str, Any]], bool], dry_run: bool = False) -> None:
        self.read_store, self.write_store, self.audit_path = read_store, write_store, audit_path
        self.gate, self.dry_run = gate, dry_run

    def _audit(self, record: dict[str, Any]) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def post_review_comment(self, *, run_id: str, item_id: str, file: str, line: int,
                            severity: str, body: str) -> dict[str, Any]:
        args = {"file": file, "line": line, "severity": severity, "body": body}
        base = {"timestamp": datetime.now(timezone.utc).isoformat(), "run_id": run_id,
                "item_id": item_id, "tool": "post_review_comment", "arguments": args}
        approved = bool(self.gate(args)); base["gate_decision"] = "approved" if approved else "denied"
        if not approved:
            self._audit({**base, "executor_validation": "not_run", "outcome": "denied"})
            raise ToolError("user declined the pending write")
        try:
            if not self.read_store.file_exists(file):
                raise ToolError(f"unknown or non-canonical file: {file}")
            candidate = (self.read_store.project_root / file).resolve()
            root = self.read_store.project_root.resolve()
            if candidate != root / file or root not in candidate.parents:
                raise ToolError("path traversal rejected by canonicalization")
            if not isinstance(line, int) or line < 1:
                raise ToolError("line must be a positive integer")
            if severity not in self.SEVERITIES:
                raise ToolError(f"invalid severity: {severity!r}")
            if not isinstance(body, str) or not (1 <= len(body) <= 500):
                raise ToolError("body length must be between 1 and 500 characters")
        except ToolError as exc:
            self._audit({**base, "executor_validation": str(exc), "outcome": "rejected"})
            raise
        if self.dry_run:
            self._audit({**base, "executor_validation": "passed", "outcome": "dry_run"})
            return {"written": False, "dry_run": True, "preview": args}
        self.write_store.append({"timestamp": base["timestamp"], "run_id": run_id, "item_id": item_id, **args})
        self._audit({**base, "executor_validation": "passed", "outcome": "written"})
        return {"written": True, "dry_run": False, "comment": args}


def gate_for(mode: GateMode, input_fn: Callable[[str], str] = input) -> Callable[[dict[str, Any]], bool]:
    if mode == "auto_approve":
        return lambda _: True
    if mode == "auto_deny":
        return lambda _: False
    return lambda args: input_fn(f"Approve write {json.dumps(args)}? [y/N] ").strip().lower() in {"y", "yes"}
