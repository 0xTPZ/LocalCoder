"""Porta futura do loop de agente orientado a missões."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol

from ..core.states import MissionState


@dataclass(frozen=True, slots=True)
class AgentContext:
    project_id: str
    mission_id: str
    state: MissionState
    values: Mapping[str, str] = field(default_factory=dict)


class AgentLoop(Protocol):
    """Uma iteração deve ser bounded, observável e interrompível."""

    def step(self, context: AgentContext) -> AgentContext:
        ...

    def stop(self, reason: str) -> None:
        ...
