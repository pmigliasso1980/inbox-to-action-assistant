import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.prompt_cache import stable_json
from capstone_incident.scorer import score
from capstone_incident.system import IncidentInput, PatternGraph, analyze, lookup_owner
from reports.monitors import run_monitors

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_CALL_FIELDS = {"ts", "run_id", "item_id", "component", "role", "call_label", "model",
                        "effort", "input_tokens", "output_tokens", "cache_read_input_tokens",
                        "cache_creation_input_tokens", "latency_ms", "stop_reason", "error", "cost_usd"}


def test_unified_call_log_has_required_fields_and_labels():
    rows = [json.loads(line) for line in (ROOT / "runs/calls.jsonl").read_text().splitlines()]
    assert rows
    assert all(REQUIRED_CALL_FIELDS <= row.keys() for row in rows)
    assert all(row["call_label"] for row in rows)


def test_all_silent_failure_monitors_pass():
    results = run_monitors()
    assert len(results) == 5
    assert all(row["ok"] for row in results)


def test_prompt_serialization_is_stable():
    assert stable_json({"b": 2, "a": 1}) == stable_json({"a": 1, "b": 2})


def test_capstone_contract_forbids_extra_input():
    with pytest.raises(ValidationError):
        IncidentInput(title="x", service="checkout", occurred_at="now", description="x", secret="no")


def test_capstone_graph_improves_repeat_pattern():
    payload = {"title": "Checkout disruption", "service": "checkout", "occurred_at": "2026-01-01T00:00:00Z",
               "description": "Connections hit the configured pool ceiling and requests waited until timeout."}
    graph = PatternGraph()
    first = analyze("a", payload, graph, stage="graph", session="one")
    repeat = analyze("b", payload, graph, stage="graph", session="two")
    assert first.recurrence_key is None
    assert repeat.recurrence_key == "checkout:database_pool_exhaustion"
    assert any(x["cross_session"] for x in graph.operations)


def test_owner_tool_fails_closed():
    assert lookup_owner("checkout") == "Payments"
    with pytest.raises(KeyError):
        lookup_owner("unknown")


def test_scorer_is_objective():
    expected = {"primary_cause": "x", "severity": "y", "remediation": "z", "owner": "o", "recurrence_key": None}
    assert score(expected, expected)["score"] == 1.0
