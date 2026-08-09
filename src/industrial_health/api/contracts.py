from __future__ import annotations

from industrial_health.mlops.risk import classify_risk


def build_service_info() -> dict[str, str]:
    """Return the stable metadata exposed at the API root."""

    return {
        "service": "industrial-equipment-health-api",
        "status": "ready",
        "documentation": "/docs",
        "health": "/health",
    }


def build_prediction_response(
    *,
    engine_id: str,
    remaining_useful_life: float,
    model_version: str,
    latency_ms: float,
) -> dict[str, float | str]:
    """Return the stable prediction response shared by API, demo, and tests."""

    rounded_rul = round(float(remaining_useful_life), 2)
    rounded_latency = round(float(latency_ms), 2)
    return {
        "engine_id": engine_id,
        "remaining_useful_life": rounded_rul,
        "risk_level": classify_risk(rounded_rul),
        "model_version": model_version,
        "latency_ms": rounded_latency,
    }
