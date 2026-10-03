"""Store durável de checkpoints; consumidores não manipulam arquivos diretamente."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from pathlib import Path
from typing import Mapping, Protocol

from ..persistence.atomic_json import AtomicJsonStore
from ..persistence.locking import FileLock
from ..schemas import SchemaRegistry
from ..state.checkpoint import CheckpointRecord


@dataclass(frozen=True, slots=True)
class Checkpoint:
    checkpoint_id: str
    project_id: str
    mission_id: str
    created_at: datetime
    step: str
    payload: Mapping[str, str] = field(default_factory=dict)


class CheckpointStoreProtocol(Protocol):
    def save(self, checkpoint: Checkpoint) -> None:
        ...

    def latest(self, project_id: str, mission_id: str) -> Checkpoint | None:
        ...


class CheckpointStoreError(RuntimeError):
    pass


class CheckpointExistsError(CheckpointStoreError):
    pass


class CheckpointNotFoundError(CheckpointStoreError):
    pass


class MultipleActiveCheckpointsError(CheckpointStoreError):
    pass


class CheckpointStore:
    """Armazena um JSON por checkpoint sob um lock de diretório.

    Criação é exclusiva; substituição exige que o arquivo já exista. Todos os dados atravessam
    o SchemaRegistry e AtomicJsonStore. Arquivos temporários nunca são promovidos
    automaticamente após crash.
    """

    _SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    ACTIVE_STATES = frozenset({"CREATED", "PAUSED", "RESUMABLE"})

    def __init__(self, root: Path, registry: SchemaRegistry | None = None) -> None:
        self.root = Path(root)
        self.registry = registry or SchemaRegistry()
        self.lock_path = self.root / ".checkpoints.lock"

    def create(self, checkpoint: CheckpointRecord) -> CheckpointRecord:
        path = self._path(checkpoint.checkpoint_id)
        with FileLock(self.lock_path, "checkpoint-store"):
            if path.exists():
                raise CheckpointExistsError(checkpoint.checkpoint_id)
            self._atomic(path).save(checkpoint.to_document())
        return checkpoint

    def replace(self, checkpoint: CheckpointRecord) -> CheckpointRecord:
        path = self._path(checkpoint.checkpoint_id)
        with FileLock(self.lock_path, "checkpoint-store"):
            if not path.exists():
                raise CheckpointNotFoundError(checkpoint.checkpoint_id)
            self._atomic(path).save(checkpoint.to_document())
        return checkpoint

    def get(self, checkpoint_id: str) -> CheckpointRecord:
        document = self._atomic(self._path(checkpoint_id)).load()
        return CheckpointRecord.from_document(document)

    def validate(self, checkpoint: CheckpointRecord) -> None:
        self.registry.validate("checkpoint", checkpoint.to_document())

    def enumerate(self, project_id: str | None = None) -> tuple[CheckpointRecord, ...]:
        records: list[CheckpointRecord] = []
        if not self.root.exists():
            return ()
        for path in sorted(self.root.glob("*.json")):
            record = CheckpointRecord.from_document(self._atomic(path).load())
            if project_id is None or record.project_id == project_id:
                records.append(record)
        return tuple(records)

    def active(self, project_id: str) -> CheckpointRecord | None:
        active = [record for record in self.enumerate(project_id) if record.lifecycle_state in self.ACTIVE_STATES]
        if len(active) > 1:
            raise MultipleActiveCheckpointsError(f"multiple active checkpoints for {project_id}")
        return active[0] if active else None

    def temporary_paths(self) -> tuple[Path, ...]:
        if not self.root.exists():
            return ()
        return tuple(sorted(self.root.glob(".*.json.*.tmp")))

    def _path(self, checkpoint_id: str) -> Path:
        if not self._SAFE_ID.fullmatch(checkpoint_id):
            raise ValueError("checkpoint_id is not a safe file identifier")
        return self.root / f"{checkpoint_id}.json"

    def _atomic(self, path: Path) -> AtomicJsonStore:
        return AtomicJsonStore(path, "checkpoint", self.registry)
