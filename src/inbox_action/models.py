from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DateStatus(StrEnum):
    RESOLVED = "resolved"
    NEEDS_CONFIRMATION = "needs_confirmation"
    NOT_PROVIDED = "not_provided"


class ActionItem(BaseModel):
    title: str = Field(min_length=1)
    due_date: date | None = None
    date_text: str | None = None
    date_status: DateStatus = DateStatus.NOT_PROVIDED
    owner: str | None = None
    reason: str = Field(min_length=1)
    evidence_quote: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class MessageAnalysis(BaseModel):
    summary: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    priority: Priority
    priority_reason: str = Field(min_length=1)
    action_items: list[ActionItem]
    needs_reply: bool


class DraftReply(BaseModel):
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)


class ReviewResult(BaseModel):
    approved: bool
    notes: list[str]
    risk_flags: list[str]


class ProcessedMessage(BaseModel):
    id: int | None = None
    sender: str
    subject: str
    body: str
    analysis: MessageAnalysis
    draft: DraftReply | None
    review: ReviewResult
    model: str
    status: str = "pending_human_review"


class ReviewEvent(BaseModel):
    id: int | None = None
    message_id: int
    event_type: str
    note: str | None = None
    before_json: str | None = None
    after_json: str | None = None
    created_at: str | None = None
