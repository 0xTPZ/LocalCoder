"""Harness v0 para resultados comparáveis sem persistir prompts ou respostas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from uuid import uuid4

from ..core.contracts import GenerationRequest, GenerationResult
from ..model_backends.errors import ModelBackendError
from ..model_backends.gateway import ModelGateway
from ..persistence.atomic_json import AtomicJsonStore
from ..schemas import SchemaRegistry
from ..state.redaction import redact
from .metrics import capture_resources


Evaluator = Callable[[GenerationResult], tuple[bool, str]]


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    test_id: str
    request: GenerationRequest
    evaluator: Evaluator
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BenchmarkRun:
    document: dict[str, Any]
    result: GenerationResult | None = field(default=None, repr=False)


class BenchmarkHarness:
    def __init__(self, gateway: ModelGateway, *, registry: SchemaRegistry | None = None) -> None:
        self.gateway = gateway
        self.registry = registry or SchemaRegistry()

    def run_case(self, case: BenchmarkCase) -> BenchmarkRun:
        benchmark_id = f"{case.test_id}-{uuid4()}"
        started_at = datetime.now(timezone.utc)
        before = capture_resources()
        result: GenerationResult | None = None
        notes = list(case.notes)
        status = "FAIL"
        error_document: dict[str, Any] | None = None
        evaluator_reason = "not executed"
        try:
            result = self.gateway.generate(case.request)
            passed, evaluator_reason = case.evaluator(result)
            status = "PASS" if passed else "FAIL"
        except ModelBackendError as exc:
            error_document = exc.to_document()
            evaluator_reason = exc.code
        after = capture_resources()
        finished_at = datetime.now(timezone.utc)
        metrics: dict[str, Any] = {
            "latency_ms": result.duration_ms if result else None,
            "time_to_first_token_ms": result.time_to_first_token_ms if result else "NOT_TESTED",
            "prompt_tokens": result.input_tokens if result else None,
            "generated_tokens": result.output_tokens if result else None,
            "tokens_per_second": (result.metrics.get("tokens_per_second") if result else None),
            "runtime_prompt_ms": (result.metrics.get("runtime_prompt_ms") if result else None),
            "runtime_prompt_tokens_per_second": (
                result.metrics.get("runtime_prompt_tokens_per_second") if result else None
            ),
            "runtime_generated_tokens_per_second": (
                result.metrics.get("runtime_generated_tokens_per_second") if result else None
            ),
            **before.to_document("before"),
            **after.to_document("after"),
        }
        document = {
            "schema_version": 1,
            "benchmark_id": benchmark_id,
            "backend_id": self.gateway.config.backend_id,
            "model_id": self.gateway.config.model_id,
            "started_at": _format_utc(started_at),
            "finished_at": _format_utc(finished_at),
            "status": status,
            "metrics": redact(metrics),
            "environment": redact(
                {
                    "runtime": self.gateway.config.runtime,
                    "endpoint": self.gateway.config.endpoint,
                    "context_window_tokens": self.gateway.config.context_window_tokens,
                    "structured_output_mode": self.gateway.config.structured_output_mode,
                    "generation_parameters": dict(self.gateway.config.generation_parameters),
                    "test_id": case.test_id,
                }
            ),
            "notes": [*notes, evaluator_reason],
        }
        if error_document is not None:
            document["metrics"]["error"] = error_document
        self.registry.validate("benchmark_result", document)
        return BenchmarkRun(document=document, result=result)

    def run(self, cases: Iterable[BenchmarkCase]) -> tuple[BenchmarkRun, ...]:
        return tuple(self.run_case(case) for case in cases)

    def persist(self, run: BenchmarkRun, path: Path) -> None:
        store = AtomicJsonStore(Path(path), "benchmark_result", self.registry)
        store.save(run.document)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
