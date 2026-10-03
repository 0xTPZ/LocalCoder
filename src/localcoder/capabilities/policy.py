"""Modelo de permissões sem execução de ferramentas nesta missão."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import FrozenSet


class Capability(StrEnum):
    FILESYSTEM_READ = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"
    PROCESS_EXECUTION = "process.execution"
    NETWORK = "network"
    BROWSER = "browser"
    SSH = "ssh"
    EMAIL = "email"
    SOCIAL = "social"


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    """Allowlist explícita; deny-by-default quando não houver capacidade."""

    allowed: FrozenSet[Capability] = field(default_factory=frozenset)

    def allows(self, capability: Capability) -> bool:
        return capability in self.allowed
