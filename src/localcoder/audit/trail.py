"""Audit trail mínimo e determinístico para testes da fundação."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, Sequence
from uuid import uuid4

from ..state.redaction import redact
from ..state.time import format_utc


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_type: str
    actor: str
    subject: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str | None = None
    mission_id: str | None = None
    action_id: str | None = None
    result: str | None = None
    reason: str | None = None
    correlation_id: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)

    def to_document(self) -> dict[str, Any]:
        safe = self.redacted()
        return {
            "schema_version": 1,
            "event_id": safe.event_id,
            "event_type": safe.event_type,
            "actor": safe.actor,
            "project_id": safe.project_id,
            "mission_id": safe.mission_id,
            "action_id": safe.action_id,
            "occurred_at": format_utc(safe.occurred_at),
            "result": safe.result,
            "reason": safe.reason,
            "correlation_id": safe.correlation_id,
            "data": dict(safe.data),
        }

    def redacted(self) -> "AuditEvent":
        return AuditEvent(
            event_type=redact_text_value(self.event_type),
            actor=redact_text_value(self.actor),
            subject=redact_text_value(self.subject),
            occurred_at=self.occurred_at,
            event_id=self.event_id,
            project_id=redact_text_value(self.project_id),
            mission_id=redact_text_value(self.mission_id),
            action_id=redact_text_value(self.action_id),
            result=redact_text_value(self.result),
            reason=redact_text_value(self.reason),
            correlation_id=redact_text_value(self.correlation_id),
            data=redact(self.data),
        )


def redact_text_value(value: str | None) -> str | None:
    if value is None:
        return None
    result = redact(value)
    return result if isinstance(result, str) else str(result)


class AuditTrail(Protocol):
    def append(self, event: AuditEvent) -> None:
        ...

    def query(self, subject: str | None = None) -> Sequence[AuditEvent]:
        ...


class MemoryAuditTrail:
    """Implementação apenas para testes; armazenamento durável virá depois."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self._events.append(event.redacted())

    def query(self, subject: str | None = None) -> Sequence[AuditEvent]:
        if subject is None:
            return tuple(self._events)
        return tuple(event for event in self._events if event.subject == subject)
