"""Deterministic reflection gate for structured code reviews."""
from __future__ import annotations
import json

TAXONOMY = {"auth_bypass","command_injection","division_by_zero","identity_comparison",
"incorrect_cache_key","infinite_loop","insecure_random","invalid_amount","missing_await",
"missing_timeout","mutable_default","non_atomic_transaction","null_dereference","off_by_one",
"path_traversal","race_condition","resource_leak","result_overwritten","sql_injection","ssrf",
"swallowed_exception","timezone_naive","unchecked_status"}
SEVERITIES = {"low","medium","high","critical"}

def check(task_input: str, draft: str) -> list[str]:
    violations=[]
    try: data=json.loads(draft)
    except json.JSONDecodeError as exc: return [f"valid_json: {exc}"]
    defects=data.get("defects") if isinstance(data,dict) else None
    if not isinstance(defects,list): return ["valid_json: defects must be an array"]
    lines=len(task_input.splitlines()); seen=set()
    if len(defects)>8: violations.append("finding_limit: more than eight findings")
    for i,d in enumerate(defects):
        if not isinstance(d,dict): violations.append(f"required_fields: finding {i} is not an object"); continue
        if d.get("category") not in TAXONOMY: violations.append(f"required_fields: finding {i} has invalid category")
        if not isinstance(d.get("line"),int) or not 1<=d.get("line",0)<=lines: violations.append(f"line_numbers_valid: finding {i}")
        if d.get("severity") not in SEVERITIES or not str(d.get("rationale","")).strip(): violations.append(f"required_fields: finding {i}")
        key=(d.get("category"),d.get("line"))
        if key in seen: violations.append(f"no_duplicate_findings: {key}")
        seen.add(key)
    return violations
