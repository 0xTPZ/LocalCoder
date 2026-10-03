"""Audit trail mínimo e determinístico para testes da fundação."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Protocol, Sequence
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_type: str
    actor: str
    subject: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: str(uuid4()))
    data: Mapping[str, str] = field(default_factory=dict)


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
        self._events.append(event)

    def query(self, subject: str | None = None) -> Sequence[AuditEvent]:
        if subject is None:
            return tuple(self._events)
        return tuple(event for event in self._events if event.subject == subject)
