import unittest
from datetime import date

from src.inbox_action.models import (
    ActionItem,
    DateStatus,
    DraftReply,
    MessageAnalysis,
    Priority,
    ReviewResult,
)
from src.inbox_action.policies import (
    enforce_analysis_policy,
    enforce_review_policy,
    is_date_text_grounded,
    is_evidence_grounded,
)


class PolicyTests(unittest.TestCase):
    def test_evidence_grounding_tolerates_surrounding_punctuation(self) -> None:
        body = "Lucía prepara el reporte y Martín revisa las cifras."

        self.assertTrue(is_evidence_grounded("Lucía prepara el reporte.", body))
        self.assertTrue(is_evidence_grounded('“Martín revisa las cifras.”', body))

    def test_purely_informational_message_discards_invented_action(self) -> None:
        analysis = MessageAnalysis(
            summary="Cierre de oficina.",
            intent="Informar",
            priority=Priority.LOW,
            priority_reason="Es informativo.",
            action_items=[
                ActionItem(
                    title="Confirmar cierre",
                    date_text="el sábado",
                    reason="Cierre programado.",
                    evidence_quote="la oficina permanecerá cerrada el sábado",
                    confidence=0.9,
                )
            ],
            needs_reply=False,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body="Para tu información, la oficina permanecerá cerrada el sábado.",
            current_date=date(2026, 8, 6),
        )

        self.assertEqual(result.action_items, [])
        self.assertEqual(result.priority, Priority.LOW)
        self.assertFalse(result.needs_reply)

    def test_informational_message_preserves_explicit_request(self) -> None:
        analysis = MessageAnalysis(
            summary="Cierre de oficina y confirmación.",
            intent="Informar y solicitar confirmación",
            priority=Priority.MEDIUM,
            priority_reason="Hay una solicitud.",
            action_items=[
                ActionItem(
                    title="Confirmar recepción",
                    reason="Fue solicitado.",
                    evidence_quote="por favor confirmá que recibiste este aviso",
                    confidence=0.9,
                )
            ],
            needs_reply=True,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body=(
                "Para tu información, la oficina cerrará el sábado; "
                "por favor confirmá que recibiste este aviso."
            ),
            current_date=date(2026, 8, 6),
        )

        self.assertEqual(len(result.action_items), 1)
        self.assertTrue(result.needs_reply)

    def test_date_grounding_tolerates_articles_but_not_inventions(self) -> None:
        body = "Podemos entregar el informe el viernes o el lunes."

        self.assertTrue(is_date_text_grounded("viernes o lunes", body))
        self.assertFalse(is_date_text_grounded("en breve", body))
        self.assertFalse(is_date_text_grounded("N/A", body))

    def test_missing_date_is_not_marked_for_confirmation(self) -> None:
        analysis = MessageAnalysis(
            summary="Revisar documento.",
            intent="Revisión",
            priority=Priority.MEDIUM,
            priority_reason="Hay una tarea.",
            action_items=[
                ActionItem(
                    title="Revisar documento",
                    date_status=DateStatus.NEEDS_CONFIRMATION,
                    reason="Fue solicitado.",
                    evidence_quote="revisá el documento",
                    confidence=0.9,
                )
            ],
            needs_reply=False,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body="Por favor revisá el documento.",
            current_date=date(2026, 8, 6),
        )

        self.assertIsNone(result.action_items[0].due_date)
        self.assertEqual(result.action_items[0].date_status, DateStatus.NOT_PROVIDED)

    def test_now_resolves_to_reference_date(self) -> None:
        analysis = MessageAnalysis(
            summary="Reiniciar servicio.",
            intent="Resolver incidente",
            priority=Priority.URGENT,
            priority_reason="Es urgente.",
            action_items=[
                ActionItem(
                    title="Reiniciar servicio",
                    date_text="ahora",
                    reason="Fue solicitado.",
                    evidence_quote="reiniciá el servicio ahora",
                    confidence=0.9,
                )
            ],
            needs_reply=True,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body="Urgente: reiniciá el servicio ahora.",
            current_date=date(2026, 8, 6),
        )

        self.assertEqual(result.action_items[0].due_date, date(2026, 8, 6))
        self.assertEqual(result.action_items[0].date_status, DateStatus.RESOLVED)

    def test_ungrounded_date_text_is_removed(self) -> None:
        for invented_text in ("N/A", "en breve"):
            with self.subTest(date_text=invented_text):
                analysis = MessageAnalysis(
                    summary="Confirmar recepción.",
                    intent="Confirmación",
                    priority=Priority.MEDIUM,
                    priority_reason="Requiere respuesta.",
                    action_items=[
                        ActionItem(
                            title="Confirmar recepción",
                            date_text=invented_text,
                            date_status=DateStatus.NEEDS_CONFIRMATION,
                            reason="Fue solicitado.",
                            evidence_quote="Confirmame si recibiste el contrato",
                            confidence=0.9,
                        )
                    ],
                    needs_reply=True,
                )

                result = enforce_analysis_policy(
                    analysis,
                    original_body="Confirmame si recibiste el contrato.",
                    current_date=date(2026, 8, 6),
                )

                item = result.action_items[0]
                self.assertIsNone(item.date_text)
                self.assertIsNone(item.due_date)
                self.assertEqual(item.date_status, DateStatus.NOT_PROVIDED)

    def test_near_resolved_deadline_sets_high_priority(self) -> None:
        analysis = MessageAnalysis(
            summary="Revisar propuesta.",
            intent="Revisión",
            priority=Priority.MEDIUM,
            priority_reason="Tiene una fecha.",
            action_items=[
                ActionItem(
                    title="Revisar propuesta",
                    date_text="antes del viernes",
                    reason="Fue solicitado.",
                    evidence_quote="revisá la propuesta antes del viernes",
                    confidence=0.9,
                )
            ],
            needs_reply=False,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body="Revisá la propuesta antes del viernes.",
            current_date=date(2026, 8, 6),
        )

        self.assertEqual(result.priority, Priority.HIGH)
        self.assertIn("24 horas", result.priority_reason)

    def test_explicit_urgency_sets_urgent_priority(self) -> None:
        analysis = MessageAnalysis(
            summary="Revisar propuesta.",
            intent="Revisión urgente",
            priority=Priority.MEDIUM,
            priority_reason="Solicitud de revisión.",
            action_items=[],
            needs_reply=False,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body="Urgente: revisá la propuesta ahora.",
            current_date=date(2026, 8, 6),
        )

        self.assertEqual(result.priority, Priority.URGENT)
        self.assertIn("urgencia explícita", result.priority_reason)

    def test_unsubstantiated_urgent_with_near_deadline_becomes_high(self) -> None:
        analysis = MessageAnalysis(
            summary="Revisar propuesta.",
            intent="Revisión",
            priority=Priority.URGENT,
            priority_reason="Parece importante.",
            action_items=[
                ActionItem(
                    title="Revisar propuesta",
                    due_date=date(2026, 8, 7),
                    reason="Fue solicitado.",
                    evidence_quote="revisá la propuesta",
                    confidence=0.9,
                )
            ],
            needs_reply=False,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body="Revisá la propuesta mañana.",
            current_date=date(2026, 8, 6),
        )

        self.assertEqual(result.priority, Priority.HIGH)

    def test_resolves_unambiguous_relative_weekdays(self) -> None:
        analysis = MessageAnalysis(
            summary="Revisar propuesta y confirmar participación.",
            intent="Revisión y confirmación",
            priority=Priority.MEDIUM,
            priority_reason="Hay acciones pendientes.",
            action_items=[
                ActionItem(
                    title="Revisar la propuesta",
                    date_text="antes del viernes",
                    owner="Pablo",
                    reason="Fue solicitado.",
                    evidence_quote="revisá la propuesta antes del viernes",
                    confidence=0.9,
                ),
                ActionItem(
                    title="Confirmar participación",
                    date_text="el lunes",
                    owner="Pablo",
                    reason="Fue solicitado.",
                    evidence_quote="confirmá si participás el lunes",
                    confidence=0.9,
                ),
            ],
            needs_reply=True,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body=(
                "Pablo, revisá la propuesta antes del viernes y confirmá si participás el lunes."
            ),
            current_date=date(2026, 8, 6),
        )

        self.assertEqual(result.action_items[0].due_date, date(2026, 8, 7))
        self.assertEqual(result.action_items[1].due_date, date(2026, 8, 10))
        self.assertTrue(
            all(item.date_status == DateStatus.RESOLVED for item in result.action_items)
        )
        self.assertEqual(result.action_items[0].date_text, "antes del viernes")

    def test_keeps_multiple_relative_dates_unresolved(self) -> None:
        analysis = MessageAnalysis(
            summary="Coordinar entrega.",
            intent="Coordinación",
            priority=Priority.MEDIUM,
            priority_reason="Fecha ambigua.",
            action_items=[
                ActionItem(
                    title="Coordinar entrega",
                    date_text="viernes o lunes",
                    reason="Hay dos alternativas.",
                    evidence_quote="viernes o lunes",
                    confidence=0.8,
                )
            ],
            needs_reply=True,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body="Podemos coordinar la entrega el viernes o lunes.",
            current_date=date(2026, 8, 6),
        )

        self.assertIsNone(result.action_items[0].due_date)
        self.assertEqual(
            result.action_items[0].date_status,
            DateStatus.NEEDS_CONFIRMATION,
        )

    def test_resolves_weekday_across_week_boundary(self) -> None:
        analysis = MessageAnalysis(
            summary="Entregar informe.",
            intent="Entrega",
            priority=Priority.MEDIUM,
            priority_reason="Tiene fecha.",
            action_items=[
                ActionItem(
                    title="Entregar informe",
                    date_text="el lunes",
                    reason="Fue solicitado.",
                    evidence_quote="entregá el informe el lunes",
                    confidence=0.9,
                )
            ],
            needs_reply=False,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body="Entregá el informe el lunes.",
            current_date=date(2026, 8, 7),
        )

        self.assertEqual(result.action_items[0].due_date, date(2026, 8, 10))
        self.assertEqual(result.action_items[0].date_status, DateStatus.RESOLVED)

    def test_quoted_evidence_preserves_confidence(self) -> None:
        body = (
            "Pablo, revisá la propuesta antes del viernes y confirmá si participás el lunes."
        )
        analysis = MessageAnalysis(
            summary="Revisión de propuesta y confirmación de participación en reunión.",
            intent="Revisar la propuesta y confirmar asistencia.",
            priority=Priority.MEDIUM,
            priority_reason="Hay acciones pendientes.",
            action_items=[
                ActionItem(
                    title="Revisar la propuesta",
                    date_text="antes del viernes",
                    owner="Pablo",
                    reason="Revisión solicitada antes de la fecha.",
                    evidence_quote='"Pablo, revisá la propuesta antes del viernes"',
                    confidence=0.9,
                ),
                ActionItem(
                    title="Confirmar participación en la reunión",
                    date_text="el lunes",
                    owner="Pablo",
                    reason="Confirmación de asistencia necesaria.",
                    evidence_quote='“y confirmá si participás el lunes”',
                    confidence=0.85,
                ),
            ],
            needs_reply=True,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body=body,
            current_date=date(2026, 8, 6),
        )

        self.assertEqual(
            [item.confidence for item in result.action_items],
            [0.9, 0.85],
        )

    def test_explicit_confirmation_requires_reply(self) -> None:
        analysis = MessageAnalysis(
            summary="Confirmar asistencia.",
            intent="Confirmacion",
            priority=Priority.HIGH,
            priority_reason="Parece inmediato.",
            action_items=[],
            needs_reply=False,
        )

        result = enforce_analysis_policy(
            analysis,
            original_body="Confirmá si participás el lunes.",
            current_date=date(2026, 8, 6),
        )

        self.assertTrue(result.needs_reply)
        self.assertEqual(result.priority, Priority.LOW)

    def test_missing_required_draft_is_rejected(self) -> None:
        review = enforce_review_policy(
            None,
            ReviewResult(approved=True, notes=[], risk_flags=[]),
            needs_reply=True,
        )

        self.assertFalse(review.approved)
        self.assertIn("missing_required_draft", review.risk_flags)

    def test_future_commitment_requires_human_approval_without_rejection(self) -> None:
        review = enforce_review_policy(
            DraftReply(
                subject="Re: Propuesta",
                body="Revisaré la propuesta y te confirmaré mi participación.",
            ),
            ReviewResult(approved=True, notes=[], risk_flags=[]),
            needs_reply=True,
        )

        self.assertTrue(review.approved)
        self.assertIn("requires_human_approval", review.risk_flags)
        self.assertNotIn("unauthorized_commitment", review.risk_flags)

    def test_future_commitment_does_not_override_reviewer_rejection(self) -> None:
        review = enforce_review_policy(
            DraftReply(
                subject="Re: Propuesta",
                body="Revisaré la propuesta y además enviaré el contrato firmado.",
            ),
            ReviewResult(
                approved=False,
                notes=["El contrato firmado no está respaldado por el mensaje."],
                risk_flags=["invented_fact"],
            ),
            needs_reply=True,
        )

        self.assertFalse(review.approved)
        self.assertIn("invented_fact", review.risk_flags)
        self.assertIn("requires_human_approval", review.risk_flags)


if __name__ == "__main__":
    unittest.main()
