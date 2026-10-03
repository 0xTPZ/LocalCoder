from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from localcoder.audit import AuditStore
from localcoder.benchmarks import BenchmarkCase, BenchmarkHarness
from localcoder.model_backends import (
    BackendTimeoutError,
    BackendUnavailableError,
    GatewayConfig,
    GenerationRequest,
    InvalidBackendResponseError,
    ModelGateway,
    ModelUnavailableError,
    OpenAICompatibleBackend,
    StructuredOutputError,
)


class FakeState:
    mode = "valid"
    delay = 0.0
    received: list[dict] = []


class FakeHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args) -> None:
        return

    def _write(self, status: int, payload: object, content_type: str = "application/json") -> None:
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError):
            return

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self._write(404, {"error": "not found"})
            return
        if FakeState.mode == "unavailable":
            self._write(503, {"error": "offline"})
            return
        self._write(200, {"status": "ok"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._write(404, {"error": "not found"})
            return
        if FakeState.delay:
            time.sleep(FakeState.delay)
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        FakeState.received.append(body)
        if FakeState.mode == "invalid_json":
            self._write(200, b"{", "application/json")
            return
        if FakeState.mode == "invalid_shape":
            self._write(200, {"choices": []})
            return
        content = "LOCALCODER_OK"
        if "response_format" in body:
            if FakeState.mode == "structured_invalid":
                content = json.dumps({"language": "rust", "answer": 4, "passed": False})
            else:
                content = json.dumps({"language": "python", "answer": 5, "passed": True})
        self._write(
            200,
            {
                "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
            },
        )


class Mission004Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.endpoint = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self) -> None:
        FakeState.mode = "valid"
        FakeState.delay = 0.0
        FakeState.received = []

    def config(self, **changes) -> GatewayConfig:
        values = {
            "backend_id": "fake-http",
            "runtime": "fake-runtime",
            "endpoint": self.endpoint,
            "model_id": "fixture-model",
            "timeout_seconds": 1.0,
            "context_window_tokens": 2048,
            "generation_parameters": {"temperature": 0.0},
        }
        values.update(changes)
        return GatewayConfig(**values)

    def test_backend_health_and_generation_normalize_openai_response(self) -> None:
        backend = OpenAICompatibleBackend(
            backend_id="fake-http",
            endpoint=self.endpoint,
            runtime="fake-runtime",
            model_id="fixture-model",
        )
        self.assertEqual(backend.health().status.value, "AVAILABLE")
        result = backend.generate(GenerationRequest("Return token"), "fixture-model")
        self.assertEqual(result.text, "LOCALCODER_OK")
        self.assertEqual(result.input_tokens, 7)
        self.assertEqual(result.output_tokens, 3)
        self.assertEqual(result.metrics["tokens_per_second"] > 0, True)

    def test_gateway_validates_structured_output_and_audits_without_payloads(self) -> None:
        with tempfile.TemporaryDirectory(prefix="localcoder-m004-") as directory:
            audit = AuditStore(Path(directory) / "audit.jsonl")
            gateway = ModelGateway(self.config(), audit=audit)
            schema = {
                "type": "object",
                "required": ["language", "answer", "passed"],
                "additionalProperties": False,
                "properties": {
                    "language": {"type": "string", "enum": ["python"]},
                    "answer": {"type": "integer", "minimum": 5},
                    "passed": {"type": "boolean"},
                },
            }
            secret_fixture = "fixture-gateway-secret"
            result = gateway.generate(
                GenerationRequest("Prompt api_key=" + secret_fixture, structured_schema=schema)
            )
            self.assertIn('"answer": 5', result.text)
            rendered = audit.path.read_text(encoding="utf-8")
            self.assertNotIn(secret_fixture, rendered)
            self.assertNotIn(result.text, rendered)
            self.assertEqual({event["event_type"] for event in audit.events()}, {"MODEL_HEALTH_CHECKED", "MODEL_GENERATION_STARTED", "MODEL_GENERATION_COMPLETED"})

    def test_unavailable_health_is_normalized_and_gateway_fails_closed(self) -> None:
        FakeState.mode = "unavailable"
        backend = OpenAICompatibleBackend("fake-http", self.endpoint, "fake-runtime", "fixture-model")
        self.assertEqual(backend.health().status.value, "UNAVAILABLE")
        with self.assertRaises(BackendUnavailableError):
            ModelGateway(self.config()).generate(GenerationRequest("must fail"))

    def test_endpoint_timeout_is_structured(self) -> None:
        FakeState.delay = 0.2
        backend = OpenAICompatibleBackend("fake-http", self.endpoint, "fake-runtime", "fixture-model", timeout_seconds=0.03)
        with self.assertRaises(BackendTimeoutError):
            backend.generate(GenerationRequest("timeout"), "fixture-model")

    def test_invalid_response_and_structured_output_are_rejected(self) -> None:
        backend = OpenAICompatibleBackend("fake-http", self.endpoint, "fake-runtime", "fixture-model")
        FakeState.mode = "invalid_json"
        with self.assertRaises(InvalidBackendResponseError):
            backend.generate(GenerationRequest("invalid"), "fixture-model")
        FakeState.mode = "invalid_shape"
        with self.assertRaises(InvalidBackendResponseError):
            backend.generate(GenerationRequest("invalid shape"), "fixture-model")
        FakeState.mode = "structured_invalid"
        gateway = ModelGateway(self.config())
        schema = {"type": "object", "required": ["answer"], "properties": {"answer": {"type": "integer", "minimum": 5}}}
        with self.assertRaises(StructuredOutputError):
            gateway.generate(GenerationRequest("invalid structured", structured_schema=schema))

    def test_model_selection_and_local_only_policy(self) -> None:
        with self.assertRaises(ModelUnavailableError):
            OpenAICompatibleBackend("fake-http", self.endpoint, "fake-runtime", "fixture-model").generate(
                GenerationRequest("wrong model"), "other-model"
            )
        with self.assertRaises(ValueError):
            GatewayConfig.from_document(
                {"backend_id": "x", "runtime": "r", "endpoint": "https://example.invalid", "model_id": "m"}
            )

    def test_benchmark_harness_validates_record_without_storing_prompt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="localcoder-m004-bench-") as directory:
            gateway = ModelGateway(self.config())
            harness = BenchmarkHarness(gateway)
            secret_fixture = "fixture-benchmark-secret"
            run = harness.run_case(
                BenchmarkCase(
                    "unit-case",
                    GenerationRequest("Prompt secret=" + secret_fixture),
                    lambda result: (result.text == "LOCALCODER_OK", "fixture matched"),
                )
            )
            output = Path(directory) / "result.json"
            harness.persist(run, output)
            self.assertEqual(run.document["status"], "PASS")
            self.assertTrue(output.is_file())
            self.assertNotIn(secret_fixture, output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
