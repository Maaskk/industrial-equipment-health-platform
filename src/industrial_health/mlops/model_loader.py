from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class RULModel(Protocol):
    def predict_one(self, features: dict[str, float]) -> float:
        """Predict Remaining Useful Life for one equipment state."""


@dataclass(frozen=True)
class FallbackRULModel:
    """Deterministic fallback for integration tests before MLflow is wired."""

    max_life_cycles: float = 130.0

    def predict_one(self, features: dict[str, float]) -> float:
        cycle = float(features.get("cycle", 0.0))
        return max(0.0, round(self.max_life_cycles - cycle, 2))


class PickleRULModel:
    def __init__(self, model: object) -> None:
        self.model = model

    def predict_one(self, features: dict[str, float]) -> float:
        feature_values = [features[key] for key in sorted(features)]
        prediction = self.model.predict([feature_values])[0]
        return round(float(prediction), 2)


def load_model(local_model_path: Path | None = None) -> RULModel:
    """Load a local model artifact, falling back to deterministic behavior."""

    if local_model_path and local_model_path.exists():
        with local_model_path.open("rb") as file:
            return PickleRULModel(pickle.load(file))
    return FallbackRULModel()

