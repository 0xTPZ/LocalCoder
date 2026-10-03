"""Identidade e lifecycle de operações para execução idempotente."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Mapping

from .ids import stable_id
from .redaction import redact
from .time import format_utc, utc_now


class OperationState(StrEnum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IdempotencyConflictError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OperationRecord:
    operation_id: str
    action_id: str
    idempotency_key: str
    state: OperationState
    created_at: Any
    started_at: Any | None = None
    completed_at: Any | None = None
    result: Mapping[str, Any] | None = None
    error: str | None = None
    retry_count: int = 0

    def to_action_document(self, task_id: str, kind: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "action_id": self.action_id,
            "task_id": task_id,
            "operation_id": self.operation_id,
            "idempotency_key": self.idempotency_key,
            "kind": kind,
            "created_at": format_utc(self.created_at),
            "started_at": format_utc(self.started_at) if self.started_at else None,
            "completed_at": format_utc(self.completed_at) if self.completed_at else None,
            "state": self.state.value,
            "retry_count": self.retry_count,
            "result": dict(self.result) if self.result is not None else None,
            "error": self.error,
        }


class IdempotencyRegistry:
    """Registry em memória para a fundação; a persistência usa AtomicJsonStore por operação."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], OperationRecord] = {}

    def begin(self, action_id: str, idempotency_key: str, *, now: Any | None = None) -> tuple[OperationRecord, bool]:
        if not action_id.strip() or not idempotency_key.strip():
            raise ValueError("action_id and idempotency_key are required")
        key = (action_id, idempotency_key)
        existing = self._records.get(key)
        if existing is not None:
            return existing, False
        timestamp = now or utc_now()
        record = OperationRecord(
            operation_id=stable_id("operation", action_id, idempotency_key),
            action_id=action_id,
            idempotency_key=idempotency_key,
            state=OperationState.STARTED,
            created_at=timestamp,
            started_at=timestamp,
        )
        self._records[key] = record
        return record, True

    def complete(self, operation_id: str, result: Mapping[str, Any], *, now: Any | None = None) -> OperationRecord:
        record = self._by_id(operation_id)
        sanitized = redact(dict(result))
        if record.state is OperationState.COMPLETED:
            if record.result != sanitized:
                raise IdempotencyConflictError("completed operation received a different result")
            return record
        if record.state not in (OperationState.STARTED, OperationState.PAUSED):
            raise IdempotencyConflictError(f"cannot complete operation in state {record.state}")
        updated = replace(record, state=OperationState.COMPLETED, completed_at=now or utc_now(), result=sanitized)
        self._records[(record.action_id, record.idempotency_key)] = updated
        return updated

    def fail(self, operation_id: str, error: str, *, now: Any | None = None) -> OperationRecord:
        record = self._by_id(operation_id)
        if record.state is OperationState.COMPLETED:
            return record
        updated = replace(record, state=OperationState.FAILED, completed_at=now or utc_now(), error=str(redact(error)), retry_count=record.retry_count + 1)
        self._records[(record.action_id, record.idempotency_key)] = updated
        return updated

    def get(self, action_id: str, idempotency_key: str) -> OperationRecord | None:
        return self._records.get((action_id, idempotency_key))

    def _by_id(self, operation_id: str) -> OperationRecord:
        for record in self._records.values():
            if record.operation_id == operation_id:
                return record
        raise KeyError(operation_id)
