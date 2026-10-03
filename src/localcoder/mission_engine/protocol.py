"""Porta do motor de missões; não há scheduler nesta fundação."""

from __future__ import annotations

from typing import Protocol

from .models import MissionSpec


class MissionEngine(Protocol):
    def validate(self, mission: MissionSpec) -> None:
        ...

    def run_next(self) -> str:
        """Executa no máximo uma unidade bounded e retorna seu identificador."""
        ...

    def pause(self, reason: str) -> None:
        ...

    def resume(self) -> None:
        ...
