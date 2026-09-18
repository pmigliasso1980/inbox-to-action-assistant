"""Reference integration pseudocode for the inbox workflow.

This module is intentionally provider-neutral and does not send messages. It demonstrates the
production boundary around ``InboxService``: idempotency, typed failures, bounded retry, dead-lettering,
and a separate approval gate before any external side effect.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, Protocol, TypeVar


class TransientIntegrationError(RuntimeError):
    """An operation may succeed later, such as a timeout, rate limit, or provider 5xx."""


class PermanentIntegrationError(RuntimeError):
    """Retrying unchanged input cannot help, such as invalid data or missing authorization."""


T = TypeVar("T")


def with_bounded_retry(
    operation: Callable[[], T],
    *,
    attempts: int = 4,
    base_delay_seconds: float = 1.0,
) -> T:
    """Retry transient failures only; propagate permanent and exhausted failures."""

    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    for attempt in range(attempts):
        try:
            return operation()
        except TransientIntegrationError:
            if attempt == attempts - 1:
                raise
            delay = min(base_delay_seconds * (2**attempt), 16.0)
            time.sleep(delay + random.uniform(0, delay * 0.1))

    raise AssertionError("the retry loop must return or raise")


@dataclass(frozen=True)
class IncomingMessage:
    provider_message_id: str
    sender: str
    subject: str
    body: str


class IdempotencyStore(Protocol):
    def result_id_for(self, key: str) -> int | None: ...

    def remember(self, key: str, result_id: int) -> None: ...


class DeadLetterStore(Protocol):
    def add(self, message: IncomingMessage, *, category: str, detail: str) -> None: ...


class ProcessingService(Protocol):
    def ingest(self, *, sender: str, subject: str, body: str) -> object: ...

    def get(self, message_id: int) -> object: ...


def process_once(
    message: IncomingMessage,
    *,
    service: ProcessingService,
    idempotency: IdempotencyStore,
    dead_letters: DeadLetterStore,
) -> object | None:
    """Process at most once and fail closed after the transient retry budget is exhausted."""

    prior_id = idempotency.result_id_for(message.provider_message_id)
    if prior_id is not None:
        return service.get(prior_id)

    if not message.provider_message_id or not message.body.strip():
        dead_letters.add(message, category="invalid_input", detail="Missing ID or empty body")
        return None

    try:
        result = with_bounded_retry(
            lambda: service.ingest(
                sender=message.sender,
                subject=message.subject,
                body=message.body,
            )
        )
    except PermanentIntegrationError as exc:
        dead_letters.add(message, category="permanent", detail=str(exc))
        return None
    except TransientIntegrationError as exc:
        dead_letters.add(message, category="retry_exhausted", detail=str(exc))
        return None

    result_id = getattr(result, "id", None)
    if result_id is None:
        dead_letters.add(message, category="invalid_result", detail="No persisted result ID")
        return None
    idempotency.remember(message.provider_message_id, result_id)
    return result


class ApprovedRecord(Protocol):
    id: int
    status: str


class ExternalDraftAdapter(Protocol):
    def create_draft(self, record: ApprovedRecord, *, idempotency_key: str) -> str: ...


def create_external_draft(record: ApprovedRecord, adapter: ExternalDraftAdapter) -> str:
    """Keep the external side effect behind an explicit, deterministic approval gate."""

    if record.status != "approved":
        raise PermanentIntegrationError("Human approval is required before creating a draft")
    return with_bounded_retry(
        lambda: adapter.create_draft(record, idempotency_key=f"approved-message:{record.id}")
    )
