"""Recovery Manager sem execução automática de ações."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..audit.store import AuditStore
from ..checkpoints.store import CheckpointStore
from ..mission_engine.journal import JournalStore
from ..persistence.jsonl import JsonlCorruptionError
from ..persistence.locking import FileLock, process_is_alive
from ..schemas import SchemaError


class RecoveryStatus(StrEnum):
    CLEAN = "CLEAN"
    RECOVERABLE = "RECOVERABLE"
    AMBIGUOUS = "AMBIGUOUS"
    CORRUPTED = "CORRUPTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    status: RecoveryStatus
    reasons: tuple[str, ...] = ()
    active_checkpoint_ids: tuple[str, ...] = ()
    ambiguous_operation_ids: tuple[str, ...] = ()
    abandoned_temporary_files: tuple[str, ...] = ()
    ignored_journal_tail: bool = False
    ignored_audit_tail: bool = False
    safe_to_resume: bool = False
    recommendation: str = "WAIT_FOR_HUMAN_DECISION"

    def to_document(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "reasons": list(self.reasons),
            "active_checkpoint_ids": list(self.active_checkpoint_ids),
            "ambiguous_operation_ids": list(self.ambiguous_operation_ids),
            "abandoned_temporary_files": list(self.abandoned_temporary_files),
            "ignored_journal_tail": self.ignored_journal_tail,
            "ignored_audit_tail": self.ignored_audit_tail,
            "safe_to_resume": self.safe_to_resume,
            "recommendation": self.recommendation,
        }


class RecoveryManager:
    """Lê estado e produz decisão; nunca repete uma operação ambígua."""

    def __init__(self, checkpoints: CheckpointStore, journal: JournalStore, audit: AuditStore | None = None) -> None:
        self.checkpoints = checkpoints
        self.journal = journal
        self.audit = audit

    def inspect(self, project_id: str | None = None) -> RecoveryReport:
        reasons: list[str] = []
        active_ids: list[str] = []
        ambiguous_ids: tuple[str, ...] = ()
        temp_files = tuple(str(path) for path in self.checkpoints.temporary_paths())
        if temp_files:
            reasons.append("abandoned checkpoint temporary file exists; it was not promoted")

        blocked = self._live_lock_reason()
        if blocked:
            return RecoveryReport(
                RecoveryStatus.BLOCKED,
                (blocked,),
                abandoned_temporary_files=temp_files,
                recommendation="WAIT_FOR_LOCK_OWNER_OR_EXPLICIT_OPERATOR_ACTION",
            )

        corrupted = False
        try:
            records = self.checkpoints.enumerate(project_id)
            active_ids = [record.checkpoint_id for record in records if record.lifecycle_state in self.checkpoints.ACTIVE_STATES]
        except (OSError, ValueError, SchemaError, RuntimeError) as exc:
            corrupted = True
            reasons.append(f"checkpoint state cannot be trusted: {type(exc).__name__}")

        if len(active_ids) > 1:
            reasons.append("multiple active checkpoints exist for the same recovery scope")
            return RecoveryReport(RecoveryStatus.AMBIGUOUS, tuple(reasons), tuple(active_ids), (), temp_files, False, False, False, "STOP_AND_REQUEST_HUMAN_DECISION")

        ignored_journal = False
        try:
            journal_report = self.journal.read()
            ignored_journal = journal_report.ignored_final_record
            if ignored_journal:
                reasons.extend(journal_report.issues)
            states: dict[str, str] = {}
            for entry in journal_report.entries:
                states[str(entry["operation_id"])] = str(entry["event"])
            ambiguous_ids = tuple(sorted(operation_id for operation_id, event in states.items() if event in {"ACTION_STARTED", "ACTION_PAUSED"}))
        except (JsonlCorruptionError, SchemaError, OSError) as exc:
            corrupted = True
            reasons.append(f"journal cannot be trusted: {type(exc).__name__}")

        ignored_audit = False
        if self.audit is not None:
            try:
                audit_report = self.audit.read()
                ignored_audit = audit_report.ignored_final_record
                if ignored_audit:
                    reasons.extend(audit_report.issues)
            except (JsonlCorruptionError, SchemaError, OSError) as exc:
                corrupted = True
                reasons.append(f"audit trail cannot be trusted: {type(exc).__name__}")

        if corrupted:
            return RecoveryReport(RecoveryStatus.CORRUPTED, tuple(reasons), tuple(active_ids), ambiguous_ids, temp_files, ignored_journal, ignored_audit, False, "PRESERVE_STATE_AND_REQUEST_REPAIR")
        if ambiguous_ids:
            reasons.append("operation has STARTED/PAUSED journal state without terminal event")
            return RecoveryReport(RecoveryStatus.AMBIGUOUS, tuple(reasons), tuple(active_ids), ambiguous_ids, temp_files, ignored_journal, ignored_audit, False, "STOP_AND_REQUEST_HUMAN_DECISION")
        if active_ids or temp_files or ignored_journal or ignored_audit:
            return RecoveryReport(RecoveryStatus.RECOVERABLE, tuple(reasons), tuple(active_ids), (), temp_files, ignored_journal, ignored_audit, bool(active_ids), "RESUME_ONLY_FROM_VALID_CHECKPOINT_AFTER_REVIEW")
        return RecoveryReport(RecoveryStatus.CLEAN, tuple(reasons), (), (), (), ignored_journal, ignored_audit, False, "NO_RECOVERY_REQUIRED")

    def _live_lock_reason(self) -> str | None:
        paths = [self.checkpoints.lock_path, self.journal.lock_path]
        if self.audit is not None:
            paths.append(self.audit.lock_path)
        for path in paths:
            info = FileLock.inspect(path)
            if info is not None and process_is_alive(info.pid):
                return f"live lock detected for {info.resource} (pid={info.pid})"
        return None
