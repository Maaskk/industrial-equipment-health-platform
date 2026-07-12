import tempfile
import unittest
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
            self.assertEqual(summary["drift"], "Insufficient production observations")


if __name__ == "__main__":
    unittest.main()
