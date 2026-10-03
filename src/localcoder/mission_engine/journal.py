"""Journal operacional append-only para distinguir conclusão de ambiguidade."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from ..persistence.jsonl import JsonlCorruptionError, append_jsonl_record, read_jsonl
from ..persistence.locking import FileLock
from ..schemas import SchemaRegistry
from ..state.redaction import redact
from ..state.time import format_utc


TERMINAL_EVENTS = frozenset({"ACTION_COMPLETED", "ACTION_FAILED"})


@dataclass(frozen=True, slots=True)
class JournalEntry:
    operation_id: str
    action_id: str
    event: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)
    journal_id: str = field(default_factory=lambda: str(uuid4()))
    sequence: int | None = None

    def to_document(self, sequence: int) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "journal_id": self.journal_id,
            "sequence": sequence,
            "operation_id": self.operation_id,
            "action_id": self.action_id,
            "event": self.event,
            "occurred_at": format_utc(self.occurred_at),
            "correlation_id": self.correlation_id,
            "data": redact(dict(self.data)),
        }


@dataclass(frozen=True, slots=True)
class JournalReadReport:
    entries: tuple[dict[str, Any], ...]
    ignored_final_record: bool
    issues: tuple[str, ...]


class JournalStore:
    """O journal nunca decide repetir uma ação; apenas registra fatos e lê o último estado."""

    def __init__(self, path: Path, registry: SchemaRegistry | None = None) -> None:
        self.path = Path(path)
        self.registry = registry or SchemaRegistry()
        self.lock_path = self.path.with_name(self.path.name + ".lock")

    def append(self, entry: JournalEntry) -> dict[str, Any]:
        with FileLock(self.lock_path, "operation-journal"):
            report = read_jsonl(self.path, "journal_entry", self.registry)
            sequence = max((int(item["sequence"]) for item in report.documents), default=0) + 1
            document = entry.to_document(sequence)
            self.registry.validate("journal_entry", document)
            append_jsonl_record(self.path, document)
        return document

    def planned(self, operation_id: str, action_id: str, **data: Any) -> dict[str, Any]:
        return self.append(JournalEntry(operation_id, action_id, "ACTION_PLANNED", data=data))

    def started(self, operation_id: str, action_id: str, **data: Any) -> dict[str, Any]:
        return self.append(JournalEntry(operation_id, action_id, "ACTION_STARTED", data=data))

    def paused(self, operation_id: str, action_id: str, **data: Any) -> dict[str, Any]:
        return self.append(JournalEntry(operation_id, action_id, "ACTION_PAUSED", data=data))

    def completed(self, operation_id: str, action_id: str, **data: Any) -> dict[str, Any]:
        return self.append(JournalEntry(operation_id, action_id, "ACTION_COMPLETED", data=data))

    def failed(self, operation_id: str, action_id: str, **data: Any) -> dict[str, Any]:
        return self.append(JournalEntry(operation_id, action_id, "ACTION_FAILED", data=data))

    def read(self) -> JournalReadReport:
        report = read_jsonl(self.path, "journal_entry", self.registry)
        previous = 0
        for entry in report.documents:
            sequence = int(entry["sequence"])
            if sequence <= previous:
                raise JsonlCorruptionError(f"journal sequence is not strictly increasing: {self.path}")
            previous = sequence
        return JournalReadReport(report.documents, report.ignored_final_record, report.issues)

    def interrupted_operations(self) -> tuple[str, ...]:
        states: dict[str, str] = {}
        for entry in self.read().entries:
            states[str(entry["operation_id"])] = str(entry["event"])
        return tuple(sorted(operation_id for operation_id, event in states.items() if event not in TERMINAL_EVENTS and event in {"ACTION_STARTED", "ACTION_PAUSED"}))
