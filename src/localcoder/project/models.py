"""Modelo mínimo de entrada de projeto."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ProjectSpec:
    project_id: str
    root_path: str
    roadmap_path: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id must not be empty")
        if not self.root_path.strip():
            raise ValueError("root_path must not be empty")
