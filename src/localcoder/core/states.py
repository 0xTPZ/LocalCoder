"""Estados explícitos da fundação."""

from enum import StrEnum


class ResourceState(StrEnum):
    """Estados conceituais mínimos do Resource Manager."""

    WORKING = "WORKING"
    PAUSING = "PAUSING"
    SLEEPING = "SLEEPING"
    RESUMING = "RESUMING"
    ERROR = "ERROR"
    WAITING = "WAITING"


class MissionState(StrEnum):
    """Estados de alto nível; o motor de transição será implementado depois."""

    PLANNED = "PLANNED"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
