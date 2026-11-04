"""Read-only, validated tools for the frozen code-review benchmark."""
from __future__ import annotations

import ast
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals" / "dataset.jsonl"
FILES = tuple(json.loads(line)["file"] for line in DATASET.read_text().splitlines() if line)


class ToolError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass
class ToolOutcome:
    value: dict[str, Any]
    confirmed: bool
    confirmation: str
    latency_ms: float


def _item(file: str) -> dict[str, Any]:
    if not isinstance(file, str) or file not in FILES:
        raise ToolError(f"unknown benchmark file: {file!r}")
    for line in DATASET.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item["file"] == file:
            return item
    raise ToolError(f"benchmark file disappeared: {file}")


def read_code(*, file: str) -> dict[str, Any]:
    item = _item(file)
    return {"file": file, "code": item["input"], "line_count": len(item["input"].splitlines())}


def _lint_findings(code: str, profile: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [{"line": exc.lineno or 1, "rule": "syntax_error", "message": str(exc)}]
    findings: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    findings.append({"line": node.lineno, "rule": "mutable_default", "message": "mutable default persists across calls"})
        if isinstance(node, ast.ExceptHandler) and node.type and isinstance(node.type, ast.Name) and node.type.id == "Exception":
            findings.append({"line": node.lineno, "rule": "broad_exception", "message": "broad Exception handler can hide operational failures"})
        if isinstance(node, ast.Compare) and any(isinstance(op, (ast.Is, ast.IsNot)) for op in node.ops):
            if any(isinstance(x, ast.Constant) and isinstance(x.value, str) for x in [node.left, *node.comparators]):
                findings.append({"line": node.lineno, "rule": "string_identity", "message": "string identity comparison is not value equality"})
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "system":
                findings.append({"line": node.lineno, "rule": "shell_execution", "message": "shell command construction requires injection review"})
            if node.func.attr == "get" and not any(k.arg == "timeout" for k in node.keywords):
                findings.append({"line": node.lineno, "rule": "network_without_timeout", "message": "network-style get call has no timeout keyword"})
    if profile in {"security", "all"}:
        patterns = [
            (r"SELECT.*\{", "sql_interpolation", "SQL appears to interpolate input"),
            (r"Path\([^\n]+\)\s*/", "unconfined_path", "joined path needs confinement validation"),
            (r"random\.randint", "predictable_random", "non-cryptographic PRNG used"),
            (r"if\s+\w+\s+or\s+", "permissive_boolean", "OR condition may bypass validation"),
        ]
        for pattern, rule, message in patterns:
            match = re.search(pattern, code)
            if match:
                line = code[: match.start()].count("\n") + 1
                findings.append({"line": line, "rule": rule, "message": message})
    return findings


def run_linter(*, file: str, profile: str) -> dict[str, Any]:
    if profile not in {"correctness", "security", "all"}:
        raise ToolError(f"invalid linter profile: {profile!r}")
    item = _item(file)
    return {"file": file, "profile": profile, "findings": _lint_findings(item["input"], profile)}


def run_tests(*, file: str, suite: str) -> dict[str, Any]:
    """Run deterministic non-executing checks; never execute model-provided code."""
    if suite not in {"compile", "static_smoke"}:
        raise ToolError(f"invalid test suite: {suite!r}")
    code = _item(file)["input"]
    stderr = ""
    try:
        compile(code, file, "exec")
        exit_code = 0
    except SyntaxError as exc:
        exit_code, stderr = 1, str(exc)
    observations = _lint_findings(code, "all") if suite == "static_smoke" else []
    return {"file": file, "suite": suite, "exit_code": exit_code, "stdout": "", "stderr": stderr, "observations": observations}


def confirm_result(name: str, value: Any) -> tuple[bool, str]:
    if not isinstance(value, dict):
        return False, "result is not an object"
    if not value:
        return False, "result object is empty"
    if name == "read_code" and (not isinstance(value.get("code"), str) or not value["code"].strip()):
        return False, "code is missing or empty"
    if name == "run_linter" and not isinstance(value.get("findings"), list):
        return False, "findings is not a list"
    if name == "run_tests":
        if not isinstance(value.get("exit_code"), int):
            return False, "exit_code is not an integer"
        if value.get("stderr") and value["exit_code"] == 0:
            return False, "stderr is non-empty despite exit_code 0"
        if value.get("suite") == "static_smoke" and not value.get("observations"):
            return False, "static smoke returned no relevant observations"
    return True, "type, emptiness, and relevance checks passed"


EXECUTORS: dict[str, Callable[..., dict[str, Any]]] = {
    "read_code": read_code,
    "run_linter": run_linter,
    "run_tests": run_tests,
}


def execute_confirmed(name: str, arguments: dict[str, Any]) -> ToolOutcome:
    if name not in EXECUTORS:
        raise ToolError(f"unknown tool: {name}")
    if not isinstance(arguments, dict):
        raise ToolError("tool arguments must be an object")
    started = time.perf_counter()
    value = EXECUTORS[name](**arguments)
    confirmed, verdict = confirm_result(name, value)
    return ToolOutcome(value, confirmed, verdict, (time.perf_counter() - started) * 1000)


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


TOOLS = [
    {
        "name": "read_code",
        "description": "Read the canonical frozen benchmark file when exact source text or line numbers must be verified. Do not call when the source has already been read in this turn.",
        "strict": True,
        "input_schema": _schema({"file": {"type": "string", "enum": list(FILES), "description": "Canonical benchmark filename to read."}}, ["file"]),
    },
    {
        "name": "run_linter",
        "description": "Run deterministic AST and pattern checks when a draft defect claim needs static evidence. Do not treat absence of findings as proof of correctness.",
        "strict": True,
        "input_schema": _schema({
            "file": {"type": "string", "enum": list(FILES), "description": "Canonical benchmark filename to inspect."},
            "profile": {"type": "string", "enum": ["correctness", "security", "all"], "description": "Fixed analyzer profile."},
        }, ["file", "profile"]),
    },
    {
        "name": "run_tests",
        "description": "Run safe deterministic compile or static-smoke checks when executable-style evidence is needed. This never executes untrusted code; do not claim it proves runtime behavior.",
        "strict": True,
        "input_schema": _schema({
            "file": {"type": "string", "enum": list(FILES), "description": "Canonical benchmark filename to test."},
            "suite": {"type": "string", "enum": ["compile", "static_smoke"], "description": "Safe fixed test suite to run."},
        }, ["file", "suite"]),
    },
]
