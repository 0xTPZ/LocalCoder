"""Portas do Resource Manager, sem heurísticas de hardware."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ..core.states import ResourceState


@dataclass(frozen=True, slots=True)
class ResourceSnapshot:
    """Observação factual; decisão de política fica em camada posterior."""

    observed_at: datetime
    ram_total_bytes: int | None = None
    ram_available_bytes: int | None = None
    vram_total_bytes: int | None = None
    vram_available_bytes: int | None = None
    cpu_percent: float | None = None
    source: str = "unknown"


@dataclass(frozen=True, slots=True)
class ResourceLease:
    lease_id: str
    acquired_at: datetime
    owner: str


class ResourceManager(Protocol):
    """Contrato futuro para pausar, dormir e retomar trabalho com segurança."""

    def state(self) -> ResourceState:
        ...

    def snapshot(self) -> ResourceSnapshot:
        ...

    def request(self, owner: str, reason: str) -> ResourceLease | None:
        ...

    def release(self, lease_id: str, reason: str) -> None:
        ...

    def transition(self, state: ResourceState, reason: str) -> None:
        ...
