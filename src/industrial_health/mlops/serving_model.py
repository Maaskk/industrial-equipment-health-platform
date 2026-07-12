from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FeatureSchemaRULModel:
    """Pickle-safe serving wrapper for a trained RUL regression pipeline."""

    pipeline: Any
    feature_names: list[str]
    metadata: dict[str, Any]

    def predict_one(self, features: dict[str, float]) -> float:
        missing = [name for name in self.feature_names if name not in features]
        extra = sorted(set(features) - set(self.feature_names))
        if missing:
            raise ValueError(f"Missing required model features: {missing[:8]}")
        if extra:
            raise ValueError(f"Unknown model features: {extra[:8]}")

        row = [[float(features[name]) for name in self.feature_names]]
        prediction = self.pipeline.predict(row)[0]
        return round(max(0.0, float(prediction)), 2)

