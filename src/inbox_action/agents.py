from typing import Any, TypeVar

from pydantic import BaseModel

from .models import DraftReply, MessageAnalysis, ReviewResult

T = TypeVar("T", bound=BaseModel)


class ModelPool:
    FALLBACKS = ("gpt-5.4-mini", "gpt-5-mini", "gpt-4o-mini")

    def __init__(self, client: Any, preferred: str = "gpt-5.6-luna") -> None:
        self.client = client
        self.candidates = tuple(dict.fromkeys((preferred, *self.FALLBACKS)))
        self.selected: str | None = None

    def parse(self, schema: type[T], *, instructions: str, input_text: str) -> T:
        candidates = (self.selected,) if self.selected else self.candidates
        denied: list[str] = []
        for model in candidates:
            try:
                response = self.client.responses.parse(
                    model=model,
                    instructions=instructions,
                    input=input_text,
                    text_format=schema,
                )
            except Exception as exc:
                if getattr(exc, "status_code", None) != 403:
                    raise
                denied.append(model)
                continue
            if response.output_parsed is None:
                raise RuntimeError(f"{model} did not produce structured output.")
            self.selected = model
            return response.output_parsed
        raise RuntimeError(f"The API key cannot access the attempted models: {', '.join(denied)}")


class AnalysisAgent:
    def __init__(self, models: ModelPool) -> None:
        self.models = models

    def run(
        self, *, sender: str, subject: str, body: str, current_date: str, timezone: str
    ) -> MessageAnalysis:
        return self.models.parse(
            MessageAnalysis,
            instructions=(
                "Analyze everyday messages and extract concrete actions. For each action, copy a verbatim "
                "quote as evidence and provide confidence from 0 to 1. Preserve temporal expressions in "
                "date_text. Use due_date only when the date is unambiguous; for relative or ambiguous "
                "dates, use date_status needs_confirmation and due_date null. Do not invent dates, people, "
                "or commitments. Urgent requires explicit urgency or an immediate consequence."
            ),
            input_text=(
                f"Current date: {current_date}\nTimezone: {timezone}\nSender: {sender}\n"
                f"Subject: {subject}\nMessage:\n{body}"
            ),
        )


class DraftAgent:
    def __init__(self, models: ModelPool) -> None:
        self.models = models

    def run(self, *, sender: str, subject: str, body: str, analysis: MessageAnalysis) -> DraftReply:
        return self.models.parse(
            DraftReply,
            instructions=(
                "Write a brief, professional, natural draft. Confirm only commitments supported by the "
                "analysis. Do not invent availability or claim that an action has already been completed. "
                "Use tentative language for commitments requiring human approval. For external or "
                "operational actions such as sending, restarting, deleting, or modifying, explicitly state "
                "that human approval is required before acting, even when urgent. Do not add actions absent "
                "from the analysis. Do not use placeholders such as [Your Name] or invent a signature; omit "
                "the signature when identity is unavailable. Do not request secrets. Reply in the language "
                "of the original message."
            ),
            input_text=(
                f"Sender: {sender}\nSubject: {subject}\nMessage:\n{body}\n\n"
                f"Validated analysis:\n{analysis.model_dump_json()}"
            ),
        )


class ReviewAgent:
    def __init__(self, models: ModelPool) -> None:
        self.models = models

    def run(self, *, body: str, analysis: MessageAnalysis, draft: DraftReply | None) -> ReviewResult:
        return self.models.parse(
            ReviewResult,
            instructions=(
                "Review consistency, safety, and usefulness. Reject drafts that invent facts, promise "
                "unauthorized actions, request secrets, or contradict the message. Make every note specific. "
                "When no reply is needed, an absent draft is valid. Reject unresolved placeholders and any "
                "additional action absent from the analysis, even if it seems useful, such as reviewing a "
                "document when the sender only requested confirmation of receipt. Never reject a draft for "
                "requesting human approval before an external action. Approve a cautious draft that says it "
                "will first verify an unknown fact; never demand immediate confirmation of an unverified "
                "receipt, availability, or outcome. If the only concern is that approval or verification "
                "delays an urgent request, the draft remains safe and should be approved. Even when the "
                "message is urgent, never recommend executing, sending, restarting, deleting, or modifying "
                "anything without explicit human authorization."
            ),
            input_text=(
                f"Message:\n{body}\n\nAnalysis:\n{analysis.model_dump_json()}\n\n"
                f"Draft:\n{draft.model_dump_json() if draft else 'Not required'}"
            ),
        )
