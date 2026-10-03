"""Adapter HTTP OpenAI-compatible, adequado ao servidor local llama.cpp."""

from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from os import environ
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from ..core.contracts import (
    BackendCapabilities,
    BackendHealth,
    BackendHealthStatus,
    GenerationRequest,
    GenerationResult,
    ModelProfile,
)
from .errors import (
    BackendTimeoutError,
    BackendUnavailableError,
    InvalidBackendResponseError,
    ModelBackendError,
    ModelUnavailableError,
)


_SAFE_GENERATION_PARAMETERS = frozenset({"temperature", "top_p", "top_k", "min_p", "seed", "repeat_penalty"})


@dataclass(frozen=True, slots=True)
class OpenAICompatibleBackend:
    """Conecta ao endpoint configurado sem possuir ou copiar o modelo."""

    backend_id: str
    endpoint: str
    runtime: str
    model_id: str
    context_window_tokens: int | None = None
    timeout_seconds: float = 120.0
    api_key_env: str | None = None
    structured_output_mode: str = "json_object"
    supports_structured_output: bool = True
    _metadata: Mapping[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        parsed = urlsplit(self.endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("endpoint must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("endpoint must not contain credentials")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.structured_output_mode not in {"json_object", "json_schema"}:
            raise ValueError("unsupported structured_output_mode")

    @property
    def base_url(self) -> str:
        parsed = urlsplit(self.endpoint)
        path = parsed.path.rstrip("/")
        return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))

    def profiles(self) -> Sequence[ModelProfile]:
        return (
            ModelProfile(
                backend_id=self.backend_id,
                model_id=self.model_id,
                context_window_tokens=self.context_window_tokens,
                supports_tools=False,
                supports_structured_output=self.supports_structured_output,
                metadata={"runtime": self.runtime, **dict(self._metadata)},
            ),
        )

    def capabilities(self, model_id: str) -> BackendCapabilities:
        self._ensure_model(model_id)
        return BackendCapabilities(
            structured_output=self.supports_structured_output,
            streaming=False,
            tools=False,
            usage_metrics=True,
            time_to_first_token=False,
        )

    def health(self, model_id: str | None = None) -> BackendHealth:
        selected_model = model_id or self.model_id
        self._ensure_model(selected_model)
        started = time.perf_counter()
        try:
            self._request_json("GET", "/health", timeout=self.timeout_seconds)
        except ModelBackendError as exc:
            status = BackendHealthStatus.UNAVAILABLE
            if isinstance(exc, BackendTimeoutError):
                status = BackendHealthStatus.DEGRADED
            return BackendHealth(
                backend_id=self.backend_id,
                runtime=self.runtime,
                model_id=selected_model,
                status=status,
                checked_at=datetime.now(timezone.utc),
                latency_ms=int((time.perf_counter() - started) * 1000),
                error_code=exc.code,
                message=str(exc),
            )
        return BackendHealth(
            backend_id=self.backend_id,
            runtime=self.runtime,
            model_id=selected_model,
            status=BackendHealthStatus.AVAILABLE,
            checked_at=datetime.now(timezone.utc),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def generate(self, request: GenerationRequest, model_id: str) -> GenerationResult:
        self._ensure_model(model_id)
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        body: dict[str, Any] = {"model": model_id, "messages": messages}
        if request.max_output_tokens is not None:
            body["max_tokens"] = request.max_output_tokens
        for key, value in request.generation_parameters.items():
            if key in _SAFE_GENERATION_PARAMETERS:
                body[key] = value
        if request.structured_schema is not None:
            if not self.supports_structured_output:
                raise ModelBackendError("structured output is not supported by this backend", code="CAPABILITY_UNAVAILABLE")
            if self.structured_output_mode == "json_object":
                body["response_format"] = {"type": "json_object", "schema": dict(request.structured_schema)}
            else:
                body["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": request.structured_schema_name,
                        "strict": True,
                        "schema": dict(request.structured_schema),
                    },
                }
        started = time.perf_counter()
        payload = self._request_json(
            "POST",
            "/v1/chat/completions",
            body,
            timeout=request.timeout_seconds or self.timeout_seconds,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        try:
            choice = payload["choices"][0]
            message = choice["message"]
            content = message["content"]
            if not isinstance(content, str) or not content.strip():
                raise TypeError("content is not a non-empty string")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise InvalidBackendResponseError("response missing choices[0].message.content") from exc
        usage = payload.get("usage") or {}
        input_tokens = _optional_int(usage.get("prompt_tokens"))
        output_tokens = _optional_int(usage.get("completion_tokens"))
        timings = payload.get("timings") if isinstance(payload.get("timings"), dict) else {}
        runtime_tokens_per_second = _optional_float(timings.get("predicted_per_second"))
        metadata: dict[str, str] = {"runtime": self.runtime}
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None:
            metadata["finish_reason"] = str(finish_reason)
        return GenerationResult(
            backend_id=self.backend_id,
            model_id=model_id,
            text=content,
            finish_reason=str(finish_reason) if finish_reason is not None else None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            metadata=metadata,
            request_id=request.request_id,
            metrics={
                "prompt_tokens": input_tokens,
                "generated_tokens": output_tokens,
                "time_to_first_token_ms": None,
                "tokens_per_second": runtime_tokens_per_second or _tokens_per_second(output_tokens, duration_ms),
                "runtime_prompt_ms": _optional_float(timings.get("prompt_ms")),
                "runtime_prompt_tokens_per_second": _optional_float(timings.get("prompt_per_second")),
                "runtime_generated_tokens_per_second": runtime_tokens_per_second,
            },
        )

    def shutdown(self) -> None:
        """O processo é gerenciado fora do gateway; não há shutdown implícito remoto."""

    def _ensure_model(self, model_id: str) -> None:
        if model_id != self.model_id:
            raise ModelUnavailableError(f"model is not configured for backend: {model_id}")

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        *,
        timeout: float,
    ) -> dict[str, Any]:
        raw_payload = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            raw_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        if self.api_key_env:
            api_key = environ.get(self.api_key_env)
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        request = Request(self.base_url + path, data=raw_payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            if exc.code in {408, 504}:
                raise BackendTimeoutError(f"backend HTTP timeout ({exc.code})") from exc
            if exc.code in {400, 404, 409, 422}:
                raise ModelUnavailableError(f"backend rejected model request ({exc.code})") from exc
            raise BackendUnavailableError(f"backend HTTP failure ({exc.code})") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise BackendTimeoutError("backend request timed out") from exc
        except URLError as exc:
            raise BackendUnavailableError("backend endpoint is unavailable") from exc
        except OSError as exc:
            raise BackendUnavailableError("backend transport failed") from exc
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidBackendResponseError("backend returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise InvalidBackendResponseError("backend response must be a JSON object")
        return parsed


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _tokens_per_second(tokens: int | None, duration_ms: int | None) -> float | None:
    if tokens is None or duration_ms is None or duration_ms <= 0:
        return None
    return round(tokens / (duration_ms / 1000), 3)


def _optional_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
