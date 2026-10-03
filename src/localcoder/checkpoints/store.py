"""Persistência abstrata para retomada idempotente."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Protocol


@dataclass(frozen=True, slots=True)
class Checkpoint:
    checkpoint_id: str
    project_id: str
    mission_id: str
    created_at: datetime
    step: str
    payload: Mapping[str, str] = field(default_factory=dict)


class CheckpointStore(Protocol):
    def save(self, checkpoint: Checkpoint) -> None:
        ...

    def latest(self, project_id: str, mission_id: str) -> Checkpoint | None:
        ...
