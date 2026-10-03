"""Porta e adapters locais substituíveis para inferência."""

from .base import (
    BackendCapabilities,
    BackendHealth,
    BackendHealthStatus,
    GenerationRequest,
    GenerationResult,
    ModelBackend,
    ModelProfile,
)
from .errors import (
    BackendTimeoutError,
    BackendUnavailableError,
    InvalidBackendResponseError,
    ModelBackendError,
    ModelUnavailableError,
    StructuredOutputError,
)
from .gateway import GatewayConfig, ModelGateway
from .openai_http import OpenAICompatibleBackend
from .structured import parse_structured_output

__all__ = [
    "BackendCapabilities",
    "BackendHealth",
    "BackendHealthStatus",
    "BackendTimeoutError",
    "BackendUnavailableError",
    "GenerationRequest",
    "GenerationResult",
    "GatewayConfig",
    "InvalidBackendResponseError",
    "ModelBackend",
    "ModelBackendError",
    "ModelProfile",
    "ModelUnavailableError",
    "ModelGateway",
    "OpenAICompatibleBackend",
    "parse_structured_output",
    "StructuredOutputError",
]
