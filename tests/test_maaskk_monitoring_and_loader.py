import tempfile
import unittest
from pathlib import Path
import pickle

from industrial_health.mlops.drift import NumericDriftReport, compute_numeric_drift
from industrial_health.mlops.model_loader import FallbackRULModel, load_model


class MaaskkMonitoringAndLoaderTests(unittest.TestCase):
    def test_compute_numeric_drift_flags_large_mean_shift(self):
        report = compute_numeric_drift(
            baseline=[10.0, 11.0, 12.0, 13.0],
            current=[40.0, 41.0, 42.0, 43.0],
            feature_name="sensor_7",
            mean_shift_threshold=5.0,
        )

        self.assertIsInstance(report, NumericDriftReport)
        self.assertEqual(report.feature_name, "sensor_7")
        self.assertTrue(report.drift_detected)
        self.assertGreater(report.absolute_mean_shift, 5.0)

    def test_compute_numeric_drift_keeps_small_shift_clean(self):
        report = compute_numeric_drift(
            baseline=[10.0, 11.0, 12.0, 13.0],
            current=[10.5, 11.5, 12.5, 13.5],
            feature_name="sensor_2",
            mean_shift_threshold=5.0,
        )

        self.assertFalse(report.drift_detected)

    def test_load_model_uses_fallback_when_registry_artifact_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            missing_path = Path(directory) / "missing-model.pkl"

            model = load_model(local_model_path=missing_path)

            self.assertIsInstance(model, FallbackRULModel)
            self.assertEqual(model.predict_one({"cycle": 120.0}), 10.0)

    def test_load_model_returns_existing_predict_one_model_without_wrapping(self):
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory) / "model.pkl"
            with model_path.open("wb") as file:
                pickle.dump(FallbackRULModel(), file)

            model = load_model(local_model_path=model_path)

            self.assertIsInstance(model, FallbackRULModel)
            self.assertEqual(model.predict_one({"cycle": 120.0}), 10.0)


if __name__ == "__main__":
    unittest.main()
