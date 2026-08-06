from datetime import date

from .agents import AnalysisAgent, DraftAgent, ModelPool, ReviewAgent
from .models import DraftReply, MessageAnalysis, ProcessedMessage, ReviewEvent
from .policies import enforce_analysis_policy, enforce_review_policy
from .storage import InboxRepository


class InboxService:
    def __init__(self, models: ModelPool, repository: InboxRepository) -> None:
        self.models = models
        self.repository = repository
        self.analysis_agent = AnalysisAgent(models)
        self.draft_agent = DraftAgent(models)
        self.review_agent = ReviewAgent(models)

    def ingest(
        self,
        *,
        sender: str,
        subject: str,
        body: str,
        current_date: date | None = None,
        timezone: str = "America/Argentina/Cordoba",
    ) -> ProcessedMessage:
        if not body.strip():
            raise ValueError("The message cannot be empty.")
        today = current_date or date.today()
        analysis = self.analysis_agent.run(
            sender=sender,
            subject=subject,
            body=body,
            current_date=today.isoformat(),
            timezone=timezone,
        )
        analysis = enforce_analysis_policy(analysis, original_body=body, current_date=today)
        draft = (
            self.draft_agent.run(sender=sender, subject=subject, body=body, analysis=analysis)
            if analysis.needs_reply
            else None
        )
        review = self.review_agent.run(body=body, analysis=analysis, draft=draft)
        review = enforce_review_policy(draft, review, needs_reply=analysis.needs_reply)
        result = ProcessedMessage(
            sender=sender,
            subject=subject,
            body=body,
            analysis=analysis,
            draft=draft,
            review=review,
            model=self.models.selected or "unknown",
            status="pending_human_review",
        )
        return self.repository.save(result)

    def get(self, message_id: int) -> ProcessedMessage:
        message = self.repository.get(message_id)
        if message is None:
            raise LookupError(f"Message {message_id} does not exist.")
        return message

    def revise(
        self,
        message_id: int,
        *,
        analysis: MessageAnalysis | None = None,
        draft: DraftReply | None = None,
        replace_draft: bool = False,
        note: str | None = None,
    ) -> ProcessedMessage:
        return self.repository.revise(
            message_id,
            analysis=analysis,
            draft=draft,
            replace_draft=replace_draft,
            note=note,
        )

    def decide(self, message_id: int, *, approved: bool, note: str | None = None) -> ProcessedMessage:
        return self.repository.decide(message_id, approved=approved, note=note)

    def history(self, message_id: int) -> list[ReviewEvent]:
        self.get(message_id)
        return self.repository.list_review_events(message_id)
