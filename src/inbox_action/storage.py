import json
import sqlite3
from pathlib import Path

from .models import DraftReply, MessageAnalysis, ProcessedMessage, ReviewEvent


class InboxRepository:
    def __init__(self, path: str | Path = "inbox.db") -> None:
        self.path = Path(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending_review',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS action_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL REFERENCES messages(id),
                    title TEXT NOT NULL,
                    due_date TEXT,
                    owner TEXT,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open'
                );
                CREATE TABLE IF NOT EXISTS review_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL REFERENCES messages(id),
                    event_type TEXT NOT NULL,
                    note TEXT,
                    before_json TEXT,
                    after_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def save(self, message: ProcessedMessage) -> ProcessedMessage:
        payload = message.model_dump(mode="json", exclude={"id"})
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO messages(sender, subject, body, result_json, status) VALUES (?, ?, ?, ?, ?)",
                (message.sender, message.subject, message.body, json.dumps(payload), message.status),
            )
            message_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO action_items(message_id, title, due_date, owner, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        message_id,
                        item.title,
                        item.due_date.isoformat() if item.due_date else None,
                        item.owner,
                        item.reason,
                    )
                    for item in message.analysis.action_items
                ],
            )
        return message.model_copy(update={"id": message_id})

    def list_messages(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, sender, subject, status, created_at FROM messages ORDER BY id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, message_id: int) -> ProcessedMessage | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, result_json, status FROM messages WHERE id = ?", (message_id,)
            ).fetchone()
        if row is None:
            return None
        payload = self._upgrade_legacy_payload(json.loads(row["result_json"]))
        payload.update({"id": row["id"], "status": row["status"]})
        return ProcessedMessage.model_validate(payload)

    @staticmethod
    def _upgrade_legacy_payload(payload: dict) -> dict:
        """Fill missing legacy fields without rewriting stored historical JSON."""
        analysis = payload.get("analysis", {})
        analysis.setdefault("priority_reason", "Not recorded in the original version.")
        for item in analysis.get("action_items", []):
            item.setdefault("evidence_quote", "Unavailable in the original record.")
            item.setdefault("confidence", 0.0)
        return payload

    def revise(
        self,
        message_id: int,
        *,
        analysis: MessageAnalysis | None = None,
        draft: DraftReply | None = None,
        replace_draft: bool = False,
        note: str | None = None,
    ) -> ProcessedMessage:
        current = self.get(message_id)
        if current is None:
            raise LookupError(f"Message {message_id} does not exist.")
        changes = {}
        if analysis is not None:
            changes["analysis"] = analysis
        if replace_draft:
            changes["draft"] = draft
        if not changes:
            raise ValueError("The revision contains no changes.")
        revised = current.model_copy(update={**changes, "status": "pending_human_review"})
        before_json = current.model_dump_json()
        after_json = revised.model_dump_json()
        payload = revised.model_dump(mode="json", exclude={"id"})
        with self._connect() as connection:
            connection.execute(
                "UPDATE messages SET result_json = ?, status = ? WHERE id = ?",
                (json.dumps(payload), revised.status, message_id),
            )
            connection.execute("DELETE FROM action_items WHERE message_id = ?", (message_id,))
            connection.executemany(
                """
                INSERT INTO action_items(message_id, title, due_date, owner, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        message_id,
                        item.title,
                        item.due_date.isoformat() if item.due_date else None,
                        item.owner,
                        item.reason,
                    )
                    for item in revised.analysis.action_items
                ],
            )
            connection.execute(
                """
                INSERT INTO review_events(message_id, event_type, note, before_json, after_json)
                VALUES (?, 'revised', ?, ?, ?)
                """,
                (message_id, note, before_json, after_json),
            )
        return revised

    def decide(self, message_id: int, *, approved: bool, note: str | None = None) -> ProcessedMessage:
        current = self.get(message_id)
        if current is None:
            raise LookupError(f"Message {message_id} does not exist.")
        status = "approved" if approved else "rejected"
        updated = current.model_copy(update={"status": status})
        payload = updated.model_dump(mode="json", exclude={"id"})
        with self._connect() as connection:
            connection.execute(
                "UPDATE messages SET result_json = ?, status = ? WHERE id = ?",
                (json.dumps(payload), status, message_id),
            )
            connection.execute(
                """
                INSERT INTO review_events(message_id, event_type, note, before_json, after_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    status,
                    note,
                    current.model_dump_json(),
                    updated.model_dump_json(),
                ),
            )
        return updated

    def list_review_events(self, message_id: int) -> list[ReviewEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM review_events WHERE message_id = ? ORDER BY id", (message_id,)
            ).fetchall()
        return [ReviewEvent.model_validate(dict(row)) for row in rows]
