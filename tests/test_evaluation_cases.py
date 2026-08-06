import json
import unittest
from datetime import date
from pathlib import Path

from src.inbox_action.models import DraftReply, MessageAnalysis, ReviewResult
from src.inbox_action.policies import enforce_analysis_policy, enforce_review_policy


CASES_PATH = Path(__file__).parents[1] / "evals" / "daily_cases.json"
CASES = {
    case["name"]: case
    for case in json.loads(CASES_PATH.read_text(encoding="utf-8"))
}


class DailyEvaluationTests(unittest.TestCase):
    def assert_case(self, name: str) -> None:
        case = CASES[name]
        analysis = enforce_analysis_policy(
            MessageAnalysis.model_validate(case["analysis"]),
            original_body=case["body"],
            current_date=date.fromisoformat(case["current_date"]),
        )
        expected = case["expected"]
        self.assertEqual(analysis.priority, expected["priority"])
        self.assertEqual(analysis.needs_reply, expected["needs_reply"])
        self.assertEqual(len(analysis.action_items), expected["action_count"])

        if "due_dates" in expected:
            self.assertEqual(
                [item.due_date.isoformat() if item.due_date else None for item in analysis.action_items],
                expected["due_dates"],
            )
        if "date_statuses" in expected:
            self.assertEqual(
                [item.date_status for item in analysis.action_items],
                expected["date_statuses"],
            )
        if "owners" in expected:
            self.assertEqual([item.owner for item in analysis.action_items], expected["owners"])
        if "review" in case:
            review = enforce_review_policy(
                DraftReply.model_validate(case["draft"]),
                ReviewResult.model_validate(case["review"]),
                needs_reply=analysis.needs_reply,
            )
            self.assertEqual(review.approved, expected["review_approved"])
            self.assertEqual(review.risk_flags, expected["review_flags"])

    def test_informational_no_action(self) -> None:
        self.assert_case("informational_no_action")

    def test_request_without_date(self) -> None:
        self.assert_case("request_without_date")

    def test_ambiguous_date(self) -> None:
        self.assert_case("ambiguous_date")

    def test_explicit_urgency(self) -> None:
        self.assert_case("explicit_urgency")

    def test_multiple_owners(self) -> None:
        self.assert_case("multiple_owners")

    def test_draft_with_unsupported_fact(self) -> None:
        self.assert_case("draft_with_unsupported_fact")

    def test_task_without_reply(self) -> None:
        self.assert_case("task_without_reply")


if __name__ == "__main__":
    unittest.main()
