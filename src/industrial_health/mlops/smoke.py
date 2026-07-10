from __future__ import annotations

import json
import os
from pathlib import Path

REQUIRED_PREDICTION_KEYS = {
    "engine_id",
    "remaining_useful_life",
    "risk_level",
    "model_version",
    "latency_ms",
}


def build_sample_payload() -> dict[str, object]:
    sample_path = Path(os.getenv("PREDICT_SAMPLE_PATH", "demo/predict_sample.json"))
    if sample_path.exists():
        return json.loads(sample_path.read_text(encoding="utf-8"))

    return {
        "engine_id": "engine_001",
        "cycle": 120,
        "features": {},
    }


def validate_prediction_response(response: dict[str, object]) -> None:
    missing = REQUIRED_PREDICTION_KEYS.difference(response)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"prediction response missing required keys: {missing_list}")

    if response["risk_level"] not in {"low", "medium", "high"}:
        raise ValueError("risk_level must be one of: low, medium, high")
