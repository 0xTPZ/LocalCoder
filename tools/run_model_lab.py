"""Executa o laboratório real da Missão 004 contra um endpoint local já iniciado."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from localcoder.audit import AuditStore
from localcoder.benchmarks import BenchmarkCase, BenchmarkHarness
from localcoder.model_backends import BackendUnavailableError, GatewayConfig, GenerationRequest, ModelGateway


STRUCTURED_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["language", "answer", "passed"],
    "properties": {
        "language": {"type": "string", "enum": ["python"]},
        "answer": {"type": "integer", "minimum": 5},
        "passed": {"type": "boolean"},
    },
}


def build_cases() -> tuple[BenchmarkCase, ...]:
    return (
        BenchmarkCase(
            "A-simple-instruction",
            GenerationRequest(
                prompt="Return exactly the token LOCALCODER_OK and nothing else.",
                max_output_tokens=32,
            ),
            lambda result: ("LOCALCODER_OK" in result.text, "exact token observed" if "LOCALCODER_OK" in result.text else "exact token not observed"),
        ),
        BenchmarkCase(
            "B-code",
            GenerationRequest(
                prompt="Read this Python expression: result = 2 + 3. Return only the final integer.",
                max_output_tokens=32,
            ),
            _code_evaluator,
        ),
        BenchmarkCase(
            "C-structured-output",
            GenerationRequest(
                prompt=(
                    "Return JSON only. The language is python, the answer to 2 + 3 is 5, and "
                    "the passed flag must be true. Follow the supplied schema exactly."
                ),
                max_output_tokens=96,
                structured_schema=STRUCTURED_SCHEMA,
                structured_schema_name="mission004_structured",
            ),
            _structured_evaluator,
        ),
        BenchmarkCase(
            "D-context",
            GenerationRequest(
                prompt=(
                    "Use only this supplied fact: the project codename is amber-otter-417. "
                    "What is the exact project codename? Return it verbatim."
                ),
                max_output_tokens=32,
            ),
            lambda result: ("amber-otter-417" in result.text, "supplied codename observed" if "amber-otter-417" in result.text else "supplied codename not observed"),
        ),
    )


def _code_evaluator(result: Any) -> tuple[bool, str]:
    passed = bool(re.search(r"(?<!\d)5(?!\d)", result.text))
    return passed, "final integer 5 observed" if passed else "final integer 5 not observed"


def _structured_evaluator(result: Any) -> tuple[bool, str]:
    try:
        value = json.loads(result.text)
    except json.JSONDecodeError:
        return False, "gateway accepted no JSON parse result"
    passed = value == {"language": "python", "answer": 5, "passed": True}
    return passed, "validated exact structured object" if passed else "structured values differ"


def run_error_probe(config: GatewayConfig) -> dict[str, Any]:
    invalid = replace(config, endpoint="http://127.0.0.1:1", preflight_health=True)
    gateway = ModelGateway(invalid)
    try:
        gateway.generate(GenerationRequest(prompt="This request must not reach a real backend."))
    except BackendUnavailableError as exc:
        return {"test_id": "E-error", "status": "PASS", "error_code": exc.code, "retryable": exc.retryable}
    except Exception as exc:  # pragma: no cover - safety classification for an unexpected adapter
        return {"test_id": "E-error", "status": "FAIL", "error_code": type(exc).__name__}
    return {"test_id": "E-error", "status": "FAIL", "error_code": "NO_ERROR"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--endpoint", default=None, help="explicit endpoint override for this experiment")
    parser.add_argument("--runtime", default=None, help="runtime label override for this experiment")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "var" / "benchmarks" / "mission004")
    args = parser.parse_args()
    config = GatewayConfig.from_file(args.config)
    if args.endpoint or args.runtime:
        config = replace(config, endpoint=args.endpoint or config.endpoint, runtime=args.runtime or config.runtime)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit = AuditStore(args.output_dir / "audit.jsonl")
    gateway = ModelGateway(config, audit=audit)
    health = gateway.health()
    if health.status.value != "AVAILABLE":
        print(json.dumps({"status": "BLOCKED", "health": health.status.value, "error_code": health.error_code}))
        return 2
    harness = BenchmarkHarness(gateway)
    runs = harness.run(build_cases())
    documents: list[dict[str, Any]] = []
    for run in runs:
        test_id = str(run.document["environment"]["test_id"])
        harness.persist(run, args.output_dir / f"{test_id}.json")
        documents.append(
            {
                "test_id": test_id,
                "status": run.document["status"],
                "notes": run.document["notes"],
                "metrics": run.document["metrics"],
            }
        )
    documents.append(run_error_probe(config))
    summary = {
        "mission": "004",
        "status": "PASS" if all(item["status"] == "PASS" for item in documents) else "FAIL",
        "backend_id": config.backend_id,
        "runtime": config.runtime,
        "model_id": config.model_id,
        "endpoint": config.endpoint,
        "tests": documents,
        "policy": {"local_only": config.local_only, "prompts_persisted": False, "responses_persisted": False},
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    gateway.shutdown()
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
