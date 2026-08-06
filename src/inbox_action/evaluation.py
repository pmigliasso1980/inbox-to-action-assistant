import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .agents import AnalysisAgent, DraftAgent, ModelPool, ReviewAgent
from .policies import (
    enforce_analysis_policy,
    enforce_review_policy,
    is_date_text_grounded,
    is_evidence_grounded,
)


def load_cases(path: Path, selected_names: list[str] | None = None) -> list[dict[str, Any]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not selected_names:
        return cases
    available = {case["name"]: case for case in cases}
    missing = [name for name in selected_names if name not in available]
    if missing:
        raise ValueError(f"Casos inexistentes: {', '.join(missing)}")
    return [available[name] for name in selected_names]


def compare_expected(
    actual: dict[str, Any], expected: dict[str, Any], original_body: str | None = None
) -> dict[str, bool]:
    checks = {}
    if "priority" in expected:
        checks["priority"] = actual["analysis"]["priority"] == expected["priority"]
    if "accepted_priorities" in expected:
        checks["priority"] = actual["analysis"]["priority"] in expected["accepted_priorities"]
    if "needs_reply" in expected:
        checks["needs_reply"] = actual["analysis"]["needs_reply"] == expected["needs_reply"]
    if "action_count" in expected:
        checks["action_count"] = len(actual["analysis"]["action_items"]) == expected[
            "action_count"
        ]
    items = actual["analysis"]["action_items"]
    if "due_dates" in expected:
        checks["due_dates"] = [item["due_date"] for item in items] == expected["due_dates"]
    if "date_statuses" in expected:
        checks["date_statuses"] = [item["date_status"] for item in items] == expected[
            "date_statuses"
        ]
    if "owners" in expected:
        actual_owners = [item["owner"] for item in items]
        checks["owners"] = sorted(actual_owners) == sorted(expected["owners"])
    if "review_approved" in expected:
        checks["review_approved"] = actual["review"]["approved"] == expected[
            "review_approved"
        ]
    if "review_flags" in expected:
        checks["review_flags"] = set(expected["review_flags"]).issubset(
            actual["review"]["risk_flags"]
        )
    draft_body = (actual.get("draft") or {}).get("body", "").casefold()
    review_text = " ".join(
        [
            *actual["review"].get("notes", []),
            *actual["review"].get("risk_flags", []),
        ]
    ).casefold()
    if "draft_required_phrases_any" in expected:
        checks["draft_required_phrases_any"] = any(
            phrase.casefold() in draft_body for phrase in expected["draft_required_phrases_any"]
        )
    if "forbidden_draft_phrases" in expected:
        found_forbidden_draft = any(
            phrase.casefold() in draft_body for phrase in expected["forbidden_draft_phrases"]
        )
        checks["draft_avoids_unsupported_claim"] = not found_forbidden_draft
        checks["review_blocks_unsupported_claim"] = not (
            found_forbidden_draft and actual["review"]["approved"]
        )
        checks["review_matches_claim_safety"] = (
            actual["review"]["approved"] != found_forbidden_draft
        )
    if "forbidden_review_phrases" in expected:
        checks["review_avoids_unsafe_advice"] = not any(
            phrase.casefold() in review_text for phrase in expected["forbidden_review_phrases"]
        )
    if "external_action_control_phrases" in expected:
        phrases = [phrase.casefold() for phrase in expected["external_action_control_phrases"]]
        draft_has_control = any(phrase in draft_body for phrase in phrases)
        review_mentions_control = any(phrase in review_text for phrase in phrases)
        checks["review_blocks_missing_external_control"] = draft_has_control or (
            not actual["review"]["approved"] and review_mentions_control
        )
        checks["review_matches_external_control"] = (
            draft_has_control and actual["review"]["approved"]
        ) or (
            not draft_has_control
            and not actual["review"]["approved"]
            and review_mentions_control
        )
    if original_body is not None:
        checks["date_text_grounded"] = all(
            item["date_text"] is None
            or is_date_text_grounded(item["date_text"], original_body)
            for item in items
        )
        if all("evidence_quote" in item for item in items):
            checks["evidence_grounded"] = all(
                is_evidence_grounded(item["evidence_quote"], original_body) for item in items
            )
    if items and all("confidence" in item for item in items):
        checks["confidence"] = all(item["confidence"] >= 0.7 for item in items)
    if actual.get("draft") is not None:
        checks["draft_has_no_placeholders"] = not (
            re.search(r"\[[^\]]+\]", draft_body)
            or "tu nombre" in draft_body
            or "your name" in draft_body
        )
    return checks


CHECK_DIMENSIONS = {
    "action_count": "extraction",
    "owners": "extraction",
    "evidence_grounded": "extraction",
    "confidence": "extraction",
    "priority": "priority",
    "due_dates": "dates",
    "date_statuses": "dates",
    "date_text_grounded": "dates",
    "needs_reply": "response",
    "draft_required_phrases_any": "draft_quality",
    "draft_avoids_unsupported_claim": "draft_quality",
    "draft_has_no_placeholders": "draft_quality",
    "review_approved": "review",
    "review_flags": "safety",
    "review_blocks_unsupported_claim": "safety",
    "review_avoids_unsafe_advice": "safety",
    "review_blocks_missing_external_control": "safety",
    "review_matches_claim_safety": "review",
    "review_matches_external_control": "review",
}


def group_dimensions(checks: dict[str, bool]) -> dict[str, bool]:
    grouped: dict[str, list[bool]] = {}
    for name, passed in checks.items():
        grouped.setdefault(CHECK_DIMENSIONS[name], []).append(passed)
    return {name: all(values) for name, values in grouped.items()}


class LiveEvaluator:
    def __init__(self, models: ModelPool) -> None:
        self.models = models
        self.analysis_agent = AnalysisAgent(models)
        self.draft_agent = DraftAgent(models)
        self.review_agent = ReviewAgent(models)

    def run_case(self, case: dict[str, Any]) -> dict[str, Any]:
        current_date = date.fromisoformat(case["current_date"])
        sender = case.get("sender", "evaluacion@example.com")
        subject = case.get("subject", case["name"])
        body = case["body"]
        analysis = self.analysis_agent.run(
            sender=sender,
            subject=subject,
            body=body,
            current_date=current_date.isoformat(),
            timezone=case.get("timezone", "America/Argentina/Cordoba"),
        )
        analysis = enforce_analysis_policy(
            analysis, original_body=body, current_date=current_date
        )
        draft = (
            self.draft_agent.run(sender=sender, subject=subject, body=body, analysis=analysis)
            if analysis.needs_reply
            else None
        )
        review = self.review_agent.run(body=body, analysis=analysis, draft=draft)
        review = enforce_review_policy(draft, review, needs_reply=analysis.needs_reply)
        actual = {
            "analysis": analysis.model_dump(mode="json"),
            "draft": draft.model_dump(mode="json") if draft else None,
            "review": review.model_dump(mode="json"),
        }
        checks = compare_expected(
            actual,
            case.get("live_expected", case["expected"]),
            original_body=body,
        )
        dimensions = group_dimensions(checks)
        return {
            "name": case["name"],
            "passed": all(checks.values()),
            "checks": checks,
            "dimensions": dimensions,
            "actual": actual,
        }

    def run(self, cases: list[dict[str, Any]]) -> dict[str, Any]:
        results = []
        for case in cases:
            try:
                results.append(self.run_case(case))
            except Exception as exc:
                results.append(
                    {
                        "name": case["name"],
                        "passed": False,
                        "checks": {},
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        passed = sum(result["passed"] for result in results)
        dimension_results: dict[str, list[bool]] = {}
        for result in results:
            for name, value in result.get("dimensions", {}).items():
                dimension_results.setdefault(name, []).append(value)
        return {
            "model": self.models.selected,
            "summary": {"passed": passed, "failed": len(results) - passed, "total": len(results)},
            "dimension_summary": {
                name: {
                    "passed": sum(values),
                    "failed": len(values) - sum(values),
                    "total": len(values),
                }
                for name, values in dimension_results.items()
            },
            "results": results,
        }
