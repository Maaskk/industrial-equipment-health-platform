import json
import tempfile
import unittest
from pathlib import Path

from industrial_health.api.contracts import build_prediction_response
from industrial_health.mlops.model_registry import ModelMetadata, resolve_model_uri
from industrial_health.mlops.monitoring import PredictionMonitor
from industrial_health.mlops.risk import classify_risk


class MaaskkMLOpsContractTests(unittest.TestCase):
    def test_classify_risk_uses_remaining_useful_life_thresholds(self):
        self.assertEqual(classify_risk(12.5), "high")
        self.assertEqual(classify_risk(45.0), "medium")
        self.assertEqual(classify_risk(120.0), "low")

    def test_resolve_model_uri_prefers_registered_model_version(self):
        metadata = ModelMetadata(name="industrial-equipment-health-model", version="7")

        self.assertEqual(resolve_model_uri(metadata), "models:/industrial-equipment-health-model/7")

    def test_build_prediction_response_exposes_merge_stable_api_contract(self):
        response = build_prediction_response(
            engine_id="engine_001",
            remaining_useful_life=24.25,
            model_version="7",
            latency_ms=8.4,
        )

        self.assertEqual(
            response,
            {
                "engine_id": "engine_001",
                "remaining_useful_life": 24.25,
                "risk_level": "high",
                "model_version": "7",
                "latency_ms": 8.4,
            },
        )

    def test_prediction_monitor_writes_one_json_line_per_prediction(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "prediction_logs.jsonl"
            monitor = PredictionMonitor(log_path)

            monitor.record_prediction(
                engine_id="engine_001",
                remaining_useful_life=24.25,
                risk_level="high",
                model_version="7",
                latency_ms=8.4,
            )

            rows = [json.loads(line) for line in log_path.read_text().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["engine_id"], "engine_001")
            self.assertEqual(rows[0]["remaining_useful_life"], 24.25)
            self.assertEqual(rows[0]["risk_level"], "high")
            self.assertEqual(rows[0]["model_version"], "7")
            self.assertEqual(rows[0]["latency_ms"], 8.4)
            self.assertIn("timestamp_utc", rows[0])


if __name__ == "__main__":
    unittest.main()
