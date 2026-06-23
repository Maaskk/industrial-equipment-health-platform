import time
from pathlib import Path
from typing import Any

from industrial_health.api.contracts import build_prediction_response
from industrial_health.mlops.model_loader import load_model
from industrial_health.mlops.model_registry import ModelMetadata, resolve_model_uri
from industrial_health.mlops.monitoring import PredictionMonitor


def create_app() -> Any:
    """Create the FastAPI app.

    FastAPI is imported inside the factory so unit tests for pure contracts can
    run even before dependencies are installed locally.
    """

    from fastapi import FastAPI
    from pydantic import BaseModel, Field

    class PredictionRequest(BaseModel):
        engine_id: str = Field(..., examples=["engine_001"])
        cycle: int = Field(..., ge=0, examples=[120])
        features: dict[str, float] = Field(default_factory=dict)

    app = FastAPI(
        title="Industrial Equipment Health Platform",
        version="0.1.0",
        description="Predictive maintenance API for industrial equipment health.",
    )
    metadata = ModelMetadata.from_environment()
    monitor = PredictionMonitor(Path("logs/prediction_logs.jsonl"))
    model = load_model(Path("models/latest/model.pkl"))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "model_name": metadata.name,
            "model_version": metadata.version,
            "model_uri": resolve_model_uri(metadata),
        }

    @app.post("/predict")
    def predict(payload: PredictionRequest) -> dict[str, float | str]:
        started = time.perf_counter()
        features = dict(payload.features)
        features["cycle"] = float(payload.cycle)
        rul = model.predict_one(features)
        latency_ms = (time.perf_counter() - started) * 1000
        response = build_prediction_response(
            engine_id=payload.engine_id,
            remaining_useful_life=rul,
            model_version=metadata.version,
            latency_ms=latency_ms,
        )
        monitor.record_prediction(**response)
        return response

    return app


app = create_app()
