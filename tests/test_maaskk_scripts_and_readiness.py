import json
import tempfile
import unittest
from pathlib import Path

from industrial_health.mlops.readiness import ReadinessItem, build_readiness_report
from industrial_health.mlops.smoke import build_sample_payload, validate_prediction_response


class MaaskkScriptsAndReadinessTests(unittest.TestCase):
    def test_build_sample_payload_matches_api_contract(self):
        payload = build_sample_payload()

        self.assertIsInstance(payload["engine_id"], str)
        self.assertTrue(payload["engine_id"])
        self.assertIsInstance(payload["cycle"], int)
        self.assertIn("sensor_1", payload["features"])

    def test_validate_prediction_response_accepts_expected_contract(self):
        response = {
            "engine_id": "engine_001",
            "remaining_useful_life": 24.25,
            "risk_level": "high",
            "model_version": "1",
            "latency_ms": 8.4,
        }

        validate_prediction_response(response)

    def test_validate_prediction_response_rejects_missing_keys(self):
        with self.assertRaises(ValueError):
            validate_prediction_response({"engine_id": "engine_001"})

    def test_build_readiness_report_writes_actionable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "readiness.json"
            report = build_readiness_report(
                output_path=output_path,
                items=[
                    ReadinessItem("api_contract", True, "API contract implemented"),
                    ReadinessItem("active_github_actions", False, "Requires workflow-scope credential"),
                ],
            )

            stored = json.loads(output_path.read_text())
            self.assertEqual(report["status"], "partial")
            self.assertEqual(stored["items"][0]["name"], "api_contract")
            self.assertFalse(stored["items"][1]["ready"])


if __name__ == "__main__":
    unittest.main()
