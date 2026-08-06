import re
import unicodedata
from datetime import date, timedelta

from .models import DateStatus, DraftReply, MessageAnalysis, Priority, ReviewResult


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _normalize_evidence(text: str) -> str:
    return _normalize(text).strip(" \t\n\r\"'“”‘’«».,;:!?¿¡")


def is_evidence_grounded(evidence_quote: str, original_body: str) -> bool:
    normalized_evidence = _normalize_evidence(evidence_quote)
    return bool(normalized_evidence) and normalized_evidence in _normalize(original_body)


def _words(text: str) -> set[str]:
    return set(re.findall(r"\w+", _normalize(text)))


DATE_STOP_WORDS = {"a", "al", "de", "del", "el", "en", "la", "las", "los", "o"}


def is_date_text_grounded(date_text: str, original_body: str) -> bool:
    normalized_date = _normalize(date_text)
    normalized_body = _normalize(original_body)
    if normalized_date in normalized_body:
        return True
    meaningful_words = _words(date_text) - DATE_STOP_WORDS
    return bool(meaningful_words) and meaningful_words.issubset(_words(original_body))


RELATIVE_DATE_WORDS = {
    "hoy",
    "manana",
    "ahora",
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
    "today",
    "tomorrow",
    "now",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}

WEEKDAYS = {
    "lunes": 0,
    "monday": 0,
    "martes": 1,
    "tuesday": 1,
    "miercoles": 2,
    "wednesday": 2,
    "jueves": 3,
    "thursday": 3,
    "viernes": 4,
    "friday": 4,
    "sabado": 5,
    "saturday": 5,
    "domingo": 6,
    "sunday": 6,
}

URGENT_WORDS = {"urgente", "urgent", "inmediatamente", "immediately", "asap", "ahora"}

REPLY_REQUESTS = (
    "confirma",
    "confirmame",
    "confirma si",
    "responde",
    "respondeme",
    "avisame",
    "hazme saber",
    "please confirm",
    "let me know",
    "reply",
)

INFORMATIONAL_MARKERS = (
    "para tu informacion",
    "para su informacion",
    "te informo",
    "les informamos",
    "for your information",
    "fyi",
)

ACTION_REQUEST_MARKERS = (
    "por favor",
    "please",
    "debes",
    "debe ",
    "necesitas",
    "necesita ",
    "revisa",
    "confirma",
    "responde",
    "avisa",
    "envia",
    "guarda",
    "completa",
    "actualiza",
    "please",
)

UNAUTHORIZED_COMMITMENTS = (
    r"\brevisare\b",
    r"\bconfirmare\b",
    r"\benviare\b",
    r"\bhare\b",
    r"\bme comprometo\b",
    r"\bi will\b",
    r"\bi'll\b",
)


def _resolve_relative_date(date_text: str, current_date: date) -> date | None:
    words = _normalize(date_text).split()
    candidates: set[date] = set()
    if "hoy" in words or "today" in words or "ahora" in words or "now" in words:
        candidates.add(current_date)
    if "manana" in words or "tomorrow" in words:
        candidates.add(current_date + timedelta(days=1))
    for target_weekday in {WEEKDAYS[word] for word in words if word in WEEKDAYS}:
        days_ahead = (target_weekday - current_date.weekday()) % 7
        candidates.add(current_date + timedelta(days=days_ahead))
    if len(candidates) != 1:
        return None
    return candidates.pop()


def enforce_analysis_policy(
    analysis: MessageAnalysis, *, original_body: str, current_date: date
) -> MessageAnalysis:
    normalized_body = _normalize(original_body)
    safe_items = []
    for item in analysis.action_items:
        if not is_evidence_grounded(item.evidence_quote, original_body):
            item = item.model_copy(update={"confidence": min(item.confidence, 0.4)})

        date_text = _normalize(item.date_text or "")
        if date_text and not is_date_text_grounded(item.date_text or "", original_body):
            item = item.model_copy(
                update={
                    "due_date": None,
                    "date_text": None,
                    "date_status": DateStatus.NOT_PROVIDED,
                }
            )
            date_text = ""
        is_relative = any(word in date_text.split() for word in RELATIVE_DATE_WORDS)
        is_past = item.due_date is not None and item.due_date < current_date
        resolved_relative = (
            _resolve_relative_date(item.date_text or "", current_date) if is_relative else None
        )
        if not date_text and item.due_date is None:
            item = item.model_copy(update={"date_status": DateStatus.NOT_PROVIDED})
        elif resolved_relative is not None:
            item = item.model_copy(
                update={"due_date": resolved_relative, "date_status": DateStatus.RESOLVED}
            )
        elif is_relative or is_past:
            item = item.model_copy(
                update={"due_date": None, "date_status": DateStatus.NEEDS_CONFIRMATION}
            )
        elif item.due_date:
            item = item.model_copy(update={"date_status": DateStatus.RESOLVED})
        safe_items.append(item)

    is_informational = any(marker in normalized_body for marker in INFORMATIONAL_MARKERS)
    has_explicit_action_request = "?" in original_body or any(
        marker in normalized_body for marker in ACTION_REQUEST_MARKERS
    )
    if is_informational and not has_explicit_action_request:
        safe_items = []

    has_explicit_urgency = bool(_words(original_body) & URGENT_WORDS)
    has_near_resolved_deadline = any(
        item.due_date is not None and 0 <= (item.due_date - current_date).days <= 1
        for item in safe_items
    )
    if is_informational and not has_explicit_action_request and not has_explicit_urgency:
        safe_priority = Priority.LOW
        priority_reason = "Baja: el mensaje es puramente informativo y no requiere ninguna acción."
    elif has_explicit_urgency:
        safe_priority = Priority.URGENT
        priority_reason = "Urgente: el mensaje contiene lenguaje de urgencia explícita."
    elif has_near_resolved_deadline:
        safe_priority = Priority.HIGH
        priority_reason = "Alta: al menos un vencimiento verificado ocurre dentro de 24 horas."
    elif analysis.priority in {Priority.HIGH, Priority.URGENT}:
        safe_priority = Priority.MEDIUM if safe_items else Priority.LOW
        priority_reason = (
            "Prioridad reducida: no hay urgencia explícita ni un vencimiento cercano verificado."
        )
    else:
        safe_priority = analysis.priority
        priority_reason = analysis.priority_reason

    reply_requested = "?" in original_body or any(
        phrase in normalized_body for phrase in REPLY_REQUESTS
    )
    needs_reply = analysis.needs_reply or reply_requested

    return analysis.model_copy(
        update={
            "action_items": safe_items,
            "priority": safe_priority,
            "priority_reason": priority_reason,
            "needs_reply": needs_reply,
        }
    )


def enforce_review_policy(
    draft: DraftReply | None, review: ReviewResult, *, needs_reply: bool
) -> ReviewResult:
    if draft is None and needs_reply:
        note = "El mensaje solicita una respuesta, pero no se generó ningún borrador."
        return review.model_copy(
            update={
                "approved": False,
                "notes": list(dict.fromkeys([*review.notes, note])),
                "risk_flags": list(dict.fromkeys([*review.risk_flags, "missing_required_draft"])),
            }
        )
    if draft is None:
        return review
    normalized = _normalize(draft.body)
    violations = [pattern for pattern in UNAUTHORIZED_COMMITMENTS if re.search(pattern, normalized)]
    if not violations:
        return review
    note = "El borrador contiene compromisos futuros y requiere aprobación humana antes de usarse."
    return review.model_copy(
        update={
            "notes": list(dict.fromkeys([*review.notes, note])),
            "risk_flags": list(dict.fromkeys([*review.risk_flags, "requires_human_approval"])),
        }
    )
