"""Modelo declarativo de uma missão verificável."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True, slots=True)
class MissionSpec:
    mission_id: str
    objective: str
    scope: Sequence[str] = field(default_factory=tuple)
    out_of_scope: Sequence[str] = field(default_factory=tuple)
    acceptance_criteria: Sequence[str] = field(default_factory=tuple)
    rollback: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name, value in (("mission_id", self.mission_id), ("objective", self.objective)):
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
