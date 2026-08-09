import tempfile
import unittest
import json
from pathlib import Path

import pandas as pd

from industrial_health.api.data_service import (
    DatasetUnavailableError,
    EngineDataService,
    InsufficientHistoryError,
    feature_row,
)
from industrial_health.mlops.model_loader import FallbackRULModel
from industrial_health.mlops.monitoring import PredictionMonitor


class FrontendDataServiceTests(unittest.TestCase):
    def test_server_side_feature_creation_matches_model_shape(self):
        rows = []
        for cycle in range(1, 6):
            row = {"cycle": cycle}
            row.update({f"setting_{index}": float(index) for index in range(1, 4)})
            row.update({f"sensor_{index}": float(index + cycle) for index in range(1, 22)})
            rows.append(row)

        features = feature_row(pd.DataFrame(rows), subset_id=4)

        self.assertEqual(len(features), 89)
        self.assertEqual(features["cycle"], 5.0)
        self.assertIn("sensor_21_roll_slope", features)

    def test_feature_creation_rejects_insufficient_history(self):
        frame = pd.DataFrame([{"cycle": cycle} for cycle in range(1, 5)])

        with self.assertRaises(InsufficientHistoryError):
            feature_row(frame, subset_id=1)

    def test_unavailable_duckdb_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = EngineDataService(
                db_path=root / "missing.duckdb",
                model=FallbackRULModel(),
                model_version="test",
                monitor=PredictionMonitor(root / "predictions.jsonl"),
                metrics_path=root / "metrics.json",
                drift_path=root / "drift.json",
            )

            with self.assertRaises(DatasetUnavailableError):
                service.engines()

    def test_monitoring_empty_state_is_honest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = EngineDataService(
                db_path=root / "missing.duckdb",
                model=FallbackRULModel(),
                model_version="test",
                monitor=PredictionMonitor(root / "predictions.jsonl"),
                metrics_path=root / "metrics.json",
                drift_path=root / "drift.json",
            )

            summary = service.monitoring_summary()

            self.assertEqual(summary["total_predictions"], 0)
            self.assertEqual(summary["drift"]["status"], "insufficient_data")
            self.assertIsNone(summary["drift"]["drift_detected"])

    def test_repeated_identical_predictions_never_claim_no_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log_path = root / "predictions.jsonl"
            record = {
                "engine_id": "FD004_204",
                "cycle": 19,
                "remaining_useful_life": 101.87,
                "risk_level": "low",
                "model_version": "6",
                "latency_ms": 10.0,
            }
            log_path.write_text(
                "\n".join(json.dumps(record) for _ in range(12)) + "\n",
                encoding="utf-8",
            )
            service = EngineDataService(
                db_path=root / "missing.duckdb",
                model=FallbackRULModel(),
                model_version="test",
                monitor=PredictionMonitor(log_path),
                metrics_path=root / "metrics.json",
                drift_path=root / "drift.json",
            )

            drift = service.monitoring_summary()["drift"]

            self.assertEqual(drift["status"], "insufficient_data")
            self.assertIsNone(drift["drift_detected"])
            self.assertEqual(drift["sample_count"], 12)
            self.assertEqual(drift["unique_observations"], 1)

    def test_varied_predictions_produce_a_traceable_drift_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log_path = root / "predictions.jsonl"
            records = [
                {
                    "engine_id": f"FD00{1 + index % 4}_{index + 1}",
                    "cycle": 10 + index,
                    "remaining_useful_life": value,
                    "risk_level": "low" if value > 70 else "medium",
                    "model_version": "6",
                    "latency_ms": 10.0 + index,
                }
                for index, value in enumerate([120, 112, 104, 96, 70, 62, 54, 46])
            ]
            log_path.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            service = EngineDataService(
                db_path=root / "missing.duckdb",
                model=FallbackRULModel(),
                model_version="test",
                monitor=PredictionMonitor(log_path),
                metrics_path=root / "metrics.json",
                drift_path=root / "drift.json",
            )

            drift = service.monitoring_summary()["drift"]

            self.assertEqual(drift["status"], "ready")
            self.assertEqual(drift["sample_count"], 8)
            self.assertEqual(drift["baseline_count"], 4)
            self.assertEqual(drift["current_count"], 4)
            self.assertEqual(drift["metric"], "predicted_rul_mean_shift")
            self.assertTrue(drift["drift_detected"])


if __name__ == "__main__":
    unittest.main()
