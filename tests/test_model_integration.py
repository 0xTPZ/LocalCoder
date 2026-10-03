"""Integração real opt-in; a suíte normal não depende de um modelo local."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from localcoder.benchmarks import BenchmarkHarness
from localcoder.model_backends import GatewayConfig, ModelGateway


@unittest.skipUnless(
    os.environ.get("LOCALCODER_RUN_REAL_MODEL") == "1" and os.environ.get("LOCALCODER_MODEL_CONFIG"),
    "real model integration is opt-in",
)
class RealModelIntegrationTests(unittest.TestCase):
    def test_first_model_lab_cases(self) -> None:
        from tools.run_model_lab import build_cases

        config = GatewayConfig.from_file(Path(os.environ["LOCALCODER_MODEL_CONFIG"]))
        gateway = ModelGateway(config)
        self.assertEqual(gateway.health().status.value, "AVAILABLE")
        runs = BenchmarkHarness(gateway).run(build_cases())
        self.assertTrue(all(run.document["status"] == "PASS" for run in runs))


if __name__ == "__main__":
    unittest.main()
