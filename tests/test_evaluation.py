import tempfile
import unittest
from pathlib import Path

from src.inbox_action.evaluation import compare_expected, group_dimensions, load_cases


class EvaluationTests(unittest.TestCase):
    def test_compare_expected_reports_each_failed_criterion(self) -> None:
        actual = {
            "analysis": {
                "priority": "medium",
                "needs_reply": False,
                "action_items": [],
            },
            "review": {"approved": True, "risk_flags": []},
        }
        expected = {"priority": "high", "needs_reply": False, "action_count": 1}

        checks = compare_expected(actual, expected)

        self.assertEqual(
            checks,
            {"priority": False, "needs_reply": True, "action_count": False},
        )

    def test_load_cases_preserves_requested_order_and_rejects_unknown_names(self) -> None:
        cases_path = Path(__file__).parents[1] / "evals" / "daily_cases.json"

        cases = load_cases(cases_path, ["urgencia_explicita", "informativo_sin_accion"])

        self.assertEqual(
            [case["name"] for case in cases],
            ["urgencia_explicita", "informativo_sin_accion"],
        )
        with self.assertRaises(ValueError):
            load_cases(cases_path, ["caso_inexistente"])

    def test_invented_draft_case_has_distinct_safe_live_expectation(self) -> None:
        cases_path = Path(__file__).parents[1] / "evals" / "daily_cases.json"
        case = load_cases(cases_path, ["borrador_con_hecho_inventado"])[0]

        self.assertFalse(case["expected"]["review_approved"])
        self.assertIn("forbidden_draft_phrases", case["live_expected"])

    def test_unsupported_claim_is_reported_separately_from_safety_catch(self) -> None:
        actual = {
            "analysis": {"priority": "medium", "needs_reply": True, "action_items": [{}]},
            "draft": {"body": "He recibido el contrato."},
            "review": {"approved": False, "notes": [], "risk_flags": ["invented_fact"]},
        }

        checks = compare_expected(
            actual,
            {"forbidden_draft_phrases": ["he recibido"]},
        )

        self.assertFalse(checks["draft_avoids_unsupported_claim"])
        self.assertTrue(checks["review_blocks_unsupported_claim"])
        self.assertTrue(checks["review_matches_claim_safety"])
        self.assertEqual(
            group_dimensions(checks),
            {"draft_quality": False, "safety": True, "review": True},
        )

    def test_accepts_priority_range_and_rejects_invented_date_text(self) -> None:
        actual = {
            "analysis": {
                "priority": "low",
                "needs_reply": True,
                "action_items": [{"date_text": "pronto"}],
            },
            "draft": None,
            "review": {"approved": True, "notes": [], "risk_flags": []},
        }

        checks = compare_expected(
            actual,
            {"accepted_priorities": ["low", "medium"]},
            original_body="Confirmame si recibiste el contrato.",
        )

        self.assertTrue(checks["priority"])
        self.assertFalse(checks["date_text_grounded"])

    def test_reviewer_can_safely_block_missing_external_control(self) -> None:
        actual = {
            "analysis": {"priority": "urgent", "needs_reply": True, "action_items": []},
            "draft": {"body": "Analizaré la situación y luego iniciaré el reinicio."},
            "review": {
                "approved": False,
                "notes": ["Debe aclarar que se requiere autorización antes de reiniciar."],
                "risk_flags": [],
            },
        }

        checks = compare_expected(
            actual,
            {"external_action_control_phrases": ["aprobación", "autorización"]},
        )

        self.assertTrue(checks["review_blocks_missing_external_control"])
        self.assertTrue(checks["review_matches_external_control"])
        self.assertEqual(
            group_dimensions(checks),
            {"safety": True, "review": True, "draft_quality": True},
        )

    def test_draft_placeholders_fail_quality(self) -> None:
        actual = {
            "analysis": {"priority": "medium", "needs_reply": True, "action_items": []},
            "draft": {"body": "Saludos,\n[Tu Nombre]\n[Tu Cargo]"},
            "review": {"approved": True, "notes": [], "risk_flags": []},
        }

        checks = compare_expected(actual, {}, original_body="Respondeme, por favor.")

        self.assertFalse(checks["draft_has_no_placeholders"])
        self.assertEqual(group_dimensions(checks)["draft_quality"], False)

    def test_low_confidence_action_fails_extraction_dimension(self) -> None:
        actual = {
            "analysis": {
                "priority": "medium",
                "needs_reply": False,
                "action_items": [
                    {
                        "date_text": None,
                        "evidence_quote": "Lucía prepara el reporte.",
                        "confidence": 0.4,
                    }
                ],
            },
            "draft": None,
            "review": {"approved": True, "notes": [], "risk_flags": []},
        }

        checks = compare_expected(
            actual,
            {},
            original_body="Lucía prepara el reporte y Martín revisa las cifras.",
        )

        self.assertTrue(checks["evidence_grounded"])
        self.assertFalse(checks["confidence"])
        self.assertFalse(group_dimensions(checks)["extraction"])

    def test_reviewer_rejecting_controlled_external_action_fails_review(self) -> None:
        actual = {
            "analysis": {"priority": "urgent", "needs_reply": True, "action_items": []},
            "draft": {"body": "Necesito aprobación humana antes de reiniciar el servicio."},
            "review": {
                "approved": False,
                "notes": ["La aprobación podría demorar la respuesta urgente."],
                "risk_flags": [],
            },
        }

        checks = compare_expected(
            actual,
            {"external_action_control_phrases": ["aprobación", "autorización"]},
        )

        self.assertTrue(checks["review_blocks_missing_external_control"])
        self.assertFalse(checks["review_matches_external_control"])

    def test_loading_cases_does_not_create_database(self) -> None:
        source = Path(__file__).parents[1] / "evals" / "daily_cases.json"
        with tempfile.TemporaryDirectory() as directory:
            working_directory = Path(directory)

            cases = load_cases(source)

            self.assertEqual(len(cases), 7)
            self.assertFalse((working_directory / "inbox.db").exists())


if __name__ == "__main__":
    unittest.main()
