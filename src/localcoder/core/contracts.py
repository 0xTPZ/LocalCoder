"""Contratos independentes de fornecedor para backends de modelo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Capacidades declaradas de um modelo sem assumir seu runtime."""

    backend_id: str
    model_id: str
    context_window_tokens: int | None = None
    supports_tools: bool = False
    supports_structured_output: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """Pedido puro de geração; não contém credenciais nem caminhos de processo."""

    prompt: str
    system_prompt: str | None = None
    max_output_tokens: int | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if self.max_output_tokens is not None and self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Resultado normalizado para permitir comparação entre backends."""

    backend_id: str
    model_id: str
    text: str
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    duration_ms: int | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


class ModelBackend(Protocol):
    """Porta mínima de um backend; implementações concretas ficam fora do núcleo."""

    @property
    def backend_id(self) -> str:
        ...

    def profiles(self) -> Sequence[ModelProfile]:
        ...

    def generate(self, request: GenerationRequest, model_id: str) -> GenerationResult:
        ...

    def shutdown(self) -> None:
        """Libera recursos do backend de forma idempotente."""
        ...
