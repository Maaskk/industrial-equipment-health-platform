from __future__ import annotations

REQUIRED_PREDICTION_KEYS = {
    "engine_id",
    "remaining_useful_life",
    "risk_level",
    "model_version",
    "latency_ms",
}


def build_sample_payload() -> dict[str, object]:
    return {
        "engine_id": "engine_001",
        "cycle": 120,
        "features": {
            "setting_1": 0.0,
            "setting_2": 0.0,
            "setting_3": 100.0,
            "sensor_1": 518.67,
            "sensor_2": 642.54,
            "sensor_3": 1589.70,
        },
    }


def validate_prediction_response(response: dict[str, object]) -> None:
    missing = REQUIRED_PREDICTION_KEYS.difference(response)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"prediction response missing required keys: {missing_list}")

    if response["risk_level"] not in {"low", "medium", "high"}:
        raise ValueError("risk_level must be one of: low, medium, high")

