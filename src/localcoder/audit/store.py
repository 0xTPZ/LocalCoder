"""Audit store JSONL append-only, redigido e reconstruível."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..persistence.jsonl import JsonlCorruptionError, JsonlReadReport, append_jsonl_record, read_jsonl
from ..persistence.locking import FileLock
from ..schemas import SchemaRegistry
from ..state.redaction import redact
from .trail import AuditEvent


@dataclass(frozen=True, slots=True)
class AuditReadReport:
    events: tuple[dict[str, Any], ...]
    ignored_final_record: bool
    issues: tuple[str, ...]


class AuditStore:
    """Um evento por linha; somente o último registro incompleto pode ser ignorado."""

    def __init__(self, path: Path, registry: SchemaRegistry | None = None) -> None:
        self.path = Path(path)
        self.registry = registry or SchemaRegistry()
        self.lock_path = self.path.with_name(self.path.name + ".lock")

    def append(self, event: AuditEvent) -> dict[str, Any]:
        document = redact(event.to_document())
        with FileLock(self.lock_path, "audit-store"):
            report = read_jsonl(self.path, "audit_event", self.registry)
            for existing in report.documents:
                if existing.get("event_id") == document.get("event_id"):
                    return existing
            sequence = max((int(item.get("sequence", 0)) for item in report.documents), default=0) + 1
            document["sequence"] = sequence
            self.registry.validate("audit_event", document)
            append_jsonl_record(self.path, document)
        return document

    def read(self) -> AuditReadReport:
        report = read_jsonl(self.path, "audit_event", self.registry)
        previous = 0
        for document in report.documents:
            sequence = int(document.get("sequence", 0))
            if sequence <= previous:
                raise JsonlCorruptionError(f"audit sequence is not strictly increasing: {self.path}")
            previous = sequence
        return AuditReadReport(report.documents, report.ignored_final_record, report.issues)

    def events(self) -> tuple[dict[str, Any], ...]:
        return self.read().events
