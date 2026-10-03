"""Reexporta a porta estável para adapters de modelo."""

from ..core.contracts import (
    BackendCapabilities,
    BackendHealth,
    BackendHealthStatus,
    GenerationRequest,
    GenerationResult,
    ModelBackend,
    ModelProfile,
)

__all__ = [
    "BackendCapabilities",
    "BackendHealth",
    "BackendHealthStatus",
    "GenerationRequest",
    "GenerationResult",
    "ModelBackend",
    "ModelProfile",
]
