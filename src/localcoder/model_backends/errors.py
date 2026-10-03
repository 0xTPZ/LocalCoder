"""Falhas normalizadas dos backends, sem transportar payloads sensíveis."""

from __future__ import annotations

from typing import Any

from ..state.redaction import redact_text


class ModelBackendError(RuntimeError):
    code = "MODEL_BACKEND_ERROR"
    retryable = False

    def __init__(self, message: str, *, code: str | None = None, retryable: bool | None = None) -> None:
        super().__init__(redact_text(str(message)))
        self.code = code or self.code
        self.retryable = self.retryable if retryable is None else retryable

    def to_document(self) -> dict[str, Any]:
        return {"code": self.code, "retryable": self.retryable, "message": str(self)}


class BackendUnavailableError(ModelBackendError):
    code = "BACKEND_UNAVAILABLE"
    retryable = True


class BackendTimeoutError(ModelBackendError):
    code = "BACKEND_TIMEOUT"
    retryable = True


class InvalidBackendResponseError(ModelBackendError):
    code = "INVALID_BACKEND_RESPONSE"


class ModelUnavailableError(ModelBackendError):
    code = "MODEL_UNAVAILABLE"
    retryable = False


class StructuredOutputError(ModelBackendError):
    code = "STRUCTURED_OUTPUT_INVALID"
