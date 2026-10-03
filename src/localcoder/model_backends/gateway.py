"""Model Gateway central: configuração, seleção, timeout, métricas e auditoria."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit
from uuid import uuid4

from ..audit import AuditEvent, AuditTrail
from ..core.contracts import BackendHealth, BackendHealthStatus, GenerationRequest, GenerationResult, ModelBackend
from ..state.redaction import redact
from .errors import BackendUnavailableError, ModelBackendError
from .openai_http import OpenAICompatibleBackend
from .structured import parse_structured_output


@dataclass(frozen=True, slots=True)
class GatewayConfig:
    backend_id: str
    runtime: str
    endpoint: str
    model_id: str
    timeout_seconds: float = 120.0
    context_window_tokens: int | None = None
    structured_output_mode: str = "json_object"
    local_only: bool = True
    api_key_env: str | None = None
    preflight_health: bool = True
    generation_parameters: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> "GatewayConfig":
        required = ("backend_id", "runtime", "endpoint", "model_id")
        missing = [key for key in required if not str(document.get(key, "")).strip()]
        if missing:
            raise ValueError(f"missing gateway configuration: {', '.join(missing)}")
        config = cls(
            backend_id=str(document["backend_id"]),
            runtime=str(document["runtime"]),
            endpoint=str(document["endpoint"]),
            model_id=str(document["model_id"]),
            timeout_seconds=float(document.get("timeout_seconds", 120.0)),
            context_window_tokens=(
                int(document["context_window_tokens"])
                if document.get("context_window_tokens") is not None
                else None
            ),
            structured_output_mode=str(document.get("structured_output_mode", "json_object")),
            local_only=bool(document.get("local_only", True)),
            api_key_env=str(document["api_key_env"]) if document.get("api_key_env") else None,
            preflight_health=bool(document.get("preflight_health", True)),
            generation_parameters=dict(document.get("generation_parameters", {})),
        )
        if config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if config.local_only:
            host = urlsplit(config.endpoint).hostname
            if host not in {"127.0.0.1", "localhost", "::1"}:
                raise ValueError("local_only gateway requires a loopback endpoint")
        return config

    @classmethod
    def from_file(cls, path: Path) -> "GatewayConfig":
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("gateway configuration must be a JSON object")
        return cls.from_document(document)

    def backend(self) -> OpenAICompatibleBackend:
        return OpenAICompatibleBackend(
            backend_id=self.backend_id,
            endpoint=self.endpoint,
            runtime=self.runtime,
            model_id=self.model_id,
            context_window_tokens=self.context_window_tokens,
            timeout_seconds=self.timeout_seconds,
            api_key_env=self.api_key_env,
            structured_output_mode=self.structured_output_mode,
        )


class ModelGateway:
    """Facade única para backends; o restante do LocalCoder não conhece HTTP/llama.cpp."""

    def __init__(
        self,
        config: GatewayConfig,
        backends: Mapping[str, ModelBackend] | None = None,
        audit: AuditTrail | None = None,
    ) -> None:
        self.config = config
        configured = dict(backends or {})
        configured.setdefault(config.backend_id, config.backend())
        self._backends = configured
        self.audit = audit

    @classmethod
    def from_config_file(cls, path: Path, audit: AuditTrail | None = None) -> "ModelGateway":
        config = GatewayConfig.from_file(path)
        return cls(config, audit=audit)

    def backend(self) -> ModelBackend:
        try:
            return self._backends[self.config.backend_id]
        except KeyError as exc:
            raise ModelBackendError("configured backend is not registered", code="BACKEND_NOT_REGISTERED") from exc

    def health(self) -> BackendHealth:
        backend = self.backend()
        health = backend.health(self.config.model_id)
        self._record(
            "MODEL_HEALTH_CHECKED",
            result=health.status.value,
            reason=health.error_code,
            data={"backend_id": health.backend_id, "model_id": health.model_id, "status": health.status.value, "latency_ms": health.latency_ms},
        )
        return health

    def generate(self, request: GenerationRequest) -> GenerationResult:
        backend = self.backend()
        request_id = request.request_id or str(uuid4())
        effective = replace(
            request,
            request_id=request_id,
            timeout_seconds=request.timeout_seconds or self.config.timeout_seconds,
            generation_parameters={**self.config.generation_parameters, **dict(request.generation_parameters)},
        )
        if self.config.preflight_health:
            health = self.health()
            if health.status is not BackendHealthStatus.AVAILABLE:
                error = BackendUnavailableError(
                    f"backend health is {health.status.value}",
                    code=health.error_code or "BACKEND_UNAVAILABLE",
                )
                self._record_failure(request_id, error)
                raise error
        self._record(
            "MODEL_GENERATION_STARTED",
            action_id=request_id,
            data={"backend_id": self.config.backend_id, "model_id": self.config.model_id},
        )
        try:
            result = backend.generate(effective, self.config.model_id)
            if effective.structured_schema is not None:
                parse_structured_output(result.text, effective.structured_schema)
                result = replace(result, metrics={**dict(result.metrics), "structured_output_valid": True})
            self._record(
                "MODEL_GENERATION_COMPLETED",
                action_id=request_id,
                result="PASS",
                data=self._safe_metrics(result),
            )
            return result
        except ModelBackendError as exc:
            self._record_failure(request_id, exc)
            raise
        except Exception as exc:
            error = ModelBackendError("unexpected model gateway failure", code="GATEWAY_FAILURE")
            self._record_failure(request_id, error, reason_type=type(exc).__name__)
            raise error from exc

    def shutdown(self) -> None:
        for backend in self._backends.values():
            backend.shutdown()

    def _safe_metrics(self, result: GenerationResult) -> dict[str, Any]:
        return redact(
            {
                "backend_id": result.backend_id,
                "model_id": result.model_id,
                "duration_ms": result.duration_ms,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "time_to_first_token_ms": result.time_to_first_token_ms,
                "metrics": dict(result.metrics),
            }
        )

    def _record_failure(self, request_id: str, error: ModelBackendError, *, reason_type: str | None = None) -> None:
        self._record(
            "MODEL_GENERATION_FAILED",
            action_id=request_id,
            result="FAIL",
            reason=error.code,
            data={"error": error.to_document(), "exception_type": reason_type},
        )

    def _record(
        self,
        event_type: str,
        *,
        action_id: str | None = None,
        result: str | None = None,
        reason: str | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> None:
        if self.audit is None:
            return
        event = AuditEvent(
            event_type=event_type,
            actor="model-gateway",
            subject="model-inference",
            occurred_at=datetime.now(timezone.utc),
            action_id=action_id,
            result=result,
            reason=reason,
            correlation_id=action_id,
            data=redact(dict(data or {})),
        )
        self.audit.append(event)
