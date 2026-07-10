from __future__ import annotations

import pickle
from collections.abc import Sequence
from dataclasses import dataclass
from os import getenv
from pathlib import Path
from typing import Protocol


class RULModel(Protocol):
    def predict_one(self, features: dict[str, float]) -> float:
        """Predict Remaining Useful Life for one equipment state."""


@dataclass(frozen=True)
class FallbackRULModel:
    """Deterministic fallback for explicit tests only."""

    max_life_cycles: float = 130.0
    feature_names: tuple[str, ...] = ("cycle",)
    metadata: dict[str, str] | None = None

    def predict_one(self, features: dict[str, float]) -> float:
        cycle = float(features.get("cycle", 0.0))
        return max(0.0, round(self.max_life_cycles - cycle, 2))


class PickleRULModel:
    def __init__(self, model: object, feature_names: Sequence[str]) -> None:
        self.model = model
        self.feature_names = list(feature_names)
        self.metadata = {"model_type": type(model).__name__, "model_version": "unknown"}

    def predict_one(self, features: dict[str, float]) -> float:
        missing = [name for name in self.feature_names if name not in features]
        extra = sorted(set(features) - set(self.feature_names))
        if missing:
            raise ValueError(f"Missing required model features: {missing[:8]}")
        if extra:
            raise ValueError(f"Unknown model features: {extra[:8]}")
        feature_values = [features[key] for key in self.feature_names]
        prediction = self.model.predict([feature_values])[0]
        return round(float(prediction), 2)


def env_flag(name: str, default: bool = False) -> bool:
    value = getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_model(
    local_model_path: Path | None = None,
    *,
    allow_fallback: bool | None = None,
    feature_names: Sequence[str] | None = None,
) -> RULModel:
    """Load a real model artifact; only use fallback when explicitly allowed."""

    if local_model_path and local_model_path.exists():
        with local_model_path.open("rb") as file:
            model = pickle.load(file)
        if hasattr(model, "predict_one"):
            return model
        if feature_names:
            return PickleRULModel(model, feature_names)
        raise TypeError(
            f"{local_model_path} does not expose predict_one and no feature schema was provided"
        )

    if allow_fallback is None:
        allow_fallback = env_flag("ALLOW_FALLBACK_MODEL", default=False)
    if allow_fallback:
        return FallbackRULModel(metadata={"model_type": "fallback", "model_version": "test-only"})

    expected = local_model_path.as_posix() if local_model_path else "model artifact"
    raise FileNotFoundError(
        f"Missing trained model artifact at {expected}. Run `python scripts/train_model.py --download` "
        "or set ALLOW_FALLBACK_MODEL=true only for tests."
    )
