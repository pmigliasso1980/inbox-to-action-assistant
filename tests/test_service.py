import json
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from src.inbox_action.agents import ModelPool
from src.inbox_action.models import (
    ActionItem,
    DateStatus,
    DraftReply,
    MessageAnalysis,
    Priority,
    ReviewResult,
)
from src.inbox_action.service import InboxService
from src.inbox_action.storage import InboxRepository


class FakeResponses:
    def __init__(self) -> None:
        self.outputs = iter(
            [
                MessageAnalysis(
                    summary="Revisar propuesta y confirmar reunion.",
                    intent="Solicitar revision y confirmacion",
                    priority=Priority.URGENT,
                    priority_reason="Parece importante.",
                    action_items=[
                        ActionItem(
                            title="Revisar propuesta",
                            due_date=date(2023, 10, 6),
                            date_text="antes del viernes",
                            date_status=DateStatus.RESOLVED,
                            owner="Pablo",
                            reason="El remitente lo solicito explicitamente.",
                            evidence_quote="Revisa la propuesta antes del viernes",
                            confidence=0.9,
                        )
                    ],
                    needs_reply=False,
                ),
                DraftReply(subject="Re: Propuesta", body="Revisaré la propuesta y te confirmaré."),
                ReviewResult(approved=True, notes=[], risk_flags=[]),
            ]
        )

    def parse(self, **kwargs):
        return SimpleNamespace(output_parsed=next(self.outputs))


class InboxServiceTests(unittest.TestCase):
    def test_processes_and_persists_message(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = InboxRepository(Path(directory) / "test.db")
            models = ModelPool(SimpleNamespace(responses=FakeResponses()), "gpt-4o-mini")
            service = InboxService(models, repo)

            result = service.ingest(
                sender="ana@example.com",
                subject="Propuesta",
                body="Revisa la propuesta antes del viernes y confirma la reunion.",
                current_date=date(2026, 8, 6),
            )

            self.assertEqual(result.id, 1)
            self.assertEqual(result.model, "gpt-4o-mini")
            self.assertTrue(result.review.approved)
            self.assertEqual(result.analysis.priority, Priority.HIGH)
            self.assertTrue(result.analysis.needs_reply)
            self.assertIsNotNone(result.draft)
            self.assertEqual(result.analysis.action_items[0].due_date, date(2026, 8, 7))
            self.assertEqual(
                result.analysis.action_items[0].date_status, DateStatus.RESOLVED
            )
            self.assertIn("requires_human_approval", result.review.risk_flags)
            self.assertEqual(result.status, "pending_human_review")
            self.assertEqual(len(repo.list_messages()), 1)

    def test_rejects_empty_message(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = InboxRepository(Path(directory) / "test.db")
            models = ModelPool(SimpleNamespace(responses=FakeResponses()), "gpt-4o-mini")
            with self.assertRaises(ValueError):
                InboxService(models, repo).ingest(sender="x", subject="x", body="  ")

    def test_revises_decides_and_audits_message(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = InboxRepository(Path(directory) / "test.db")
            models = ModelPool(SimpleNamespace(responses=FakeResponses()), "gpt-4o-mini")
            service = InboxService(models, repo)
            created = service.ingest(
                sender="ana@example.com",
                subject="Propuesta",
                body="Revisa la propuesta antes del viernes y confirma la reunion.",
                current_date=date(2026, 8, 6),
            )
            corrected = created.analysis.model_copy(
                update={"summary": "Revisar la propuesta y responder a Ana."}
            )

            revised = service.revise(
                created.id,
                analysis=corrected,
                draft=DraftReply(
                    subject="Re: Propuesta",
                    body="Gracias, revisaré la propuesta antes de confirmar.",
                ),
                replace_draft=True,
                note="The scope was clarified.",
            )
            approved = service.decide(created.id, approved=True, note="Verificado por Pablo.")

            self.assertEqual(revised.status, "pending_human_review")
            self.assertEqual(revised.analysis.summary, corrected.summary)
            self.assertEqual(approved.status, "approved")
            self.assertEqual(service.get(created.id).status, "approved")
            events = service.history(created.id)
            self.assertEqual([event.event_type for event in events], ["revised", "approved"])
            self.assertEqual(events[1].note, "Verificado por Pablo.")

    def test_revising_unknown_message_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = InboxRepository(Path(directory) / "test.db")
            service = InboxService(ModelPool(None), repo)

            with self.assertRaises(LookupError):
                service.decide(999, approved=False, note="It does not exist.")

    def test_reads_legacy_message_without_rewriting_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.db"
            repo = InboxRepository(path)
            payload = {
                "sender": "legacy@example.com",
                "subject": "Legacy record",
                "body": "Review the document.",
                "analysis": {
                    "summary": "Review it.",
                    "intent": "Request",
                    "priority": "medium",
                    "action_items": [
                        {
                            "title": "Review document",
                            "reason": "It was requested.",
                            "date_status": "not_provided",
                        }
                    ],
                    "needs_reply": False,
                },
                "draft": None,
                "review": {"approved": True, "notes": [], "risk_flags": []},
                "model": "legacy-model",
                "status": "pending_review",
            }
            with sqlite3.connect(path) as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO messages(sender, subject, body, result_json, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("legacy@example.com", "Legacy record", "Review the document.", json.dumps(payload), "pending_review"),
                )
                message_id = int(cursor.lastrowid)

            restored = repo.get(message_id)

            self.assertIsNotNone(restored)
            self.assertEqual(restored.analysis.action_items[0].confidence, 0.0)
            self.assertIn("original version", restored.analysis.priority_reason)


if __name__ == "__main__":
    unittest.main()
