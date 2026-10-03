"""Contrato persistível e verificável de checkpoint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .time import format_utc, parse_utc


@dataclass(frozen=True, slots=True)
class CheckpointRecord:
    checkpoint_id: str
    project_id: str
    roadmap_id: str
    mission_id: str
    task_id: str
    action_id: str
    created_at: Any
    lifecycle_state: str
    completed_steps: tuple[str, ...] = ()
    in_progress_step: str | None = None
    pause_reason: str | None = None
    next_action: str | None = None
    backend_id: str | None = None
    model_id: str | None = None
    active_capabilities: tuple[str, ...] = ()
    operation_id: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_document(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "checkpoint_id": self.checkpoint_id,
            "project_id": self.project_id,
            "roadmap_id": self.roadmap_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "action_id": self.action_id,
            "created_at": format_utc(self.created_at),
            "lifecycle_state": self.lifecycle_state,
            "completed_steps": list(self.completed_steps),
            "in_progress_step": self.in_progress_step,
            "pause_reason": self.pause_reason,
            "next_action": self.next_action,
            "backend_id": self.backend_id,
            "model_id": self.model_id,
            "active_capabilities": list(self.active_capabilities),
            "operation_id": self.operation_id,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> "CheckpointRecord":
        return cls(
            checkpoint_id=document["checkpoint_id"],
            project_id=document["project_id"],
            roadmap_id=document["roadmap_id"],
            mission_id=document["mission_id"],
            task_id=document["task_id"],
            action_id=document["action_id"],
            created_at=parse_utc(document["created_at"]),
            lifecycle_state=document["lifecycle_state"],
            completed_steps=tuple(document["completed_steps"]),
            in_progress_step=document["in_progress_step"],
            pause_reason=document["pause_reason"],
            next_action=document["next_action"],
            backend_id=document["backend_id"],
            model_id=document["model_id"],
            active_capabilities=tuple(document["active_capabilities"]),
            operation_id=document["operation_id"],
            payload=dict(document.get("payload", {})),
        )
