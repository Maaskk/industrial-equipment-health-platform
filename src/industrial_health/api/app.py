import json
import os
import time
from pathlib import Path
from typing import Any

from industrial_health.api.contracts import build_prediction_response
from industrial_health.mlops.model_loader import env_flag, load_model
from industrial_health.mlops.model_registry import ModelMetadata, resolve_model_uri
from industrial_health.mlops.monitoring import PredictionMonitor


def load_feature_names(schema_path: Path, model: Any) -> list[str]:
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required = schema.get("required")
        if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
            raise RuntimeError(f"Invalid feature schema at {schema_path}")
        return required

    model_features = getattr(model, "feature_names", None)
    if model_features:
        return list(model_features)

    raise RuntimeError(
        f"Missing feature schema at {schema_path}. Run `python scripts/train_model.py --download`."
    )


def create_app(
    *,
    model_path: Path | None = None,
    schema_path: Path | None = None,
    monitor_path: Path | None = None,
    allow_fallback: bool | None = None,
) -> Any:
    """Create the FastAPI app.

    FastAPI is imported inside the factory so unit tests for pure contracts can
    run even before dependencies are installed locally.
    """

    from fastapi import FastAPI, HTTPException
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
    resolved_model_path = model_path or Path(os.getenv("MODEL_PATH", "models/latest/model.pkl"))
    resolved_schema_path = schema_path or Path(
        os.getenv("FEATURE_SCHEMA_PATH", "models/latest/feature_schema.json")
    )
    resolved_monitor_path = monitor_path or Path(
        os.getenv("PREDICTION_LOG_PATH", "logs/prediction_logs.jsonl")
    )
    fallback_enabled = env_flag("ALLOW_FALLBACK_MODEL") if allow_fallback is None else allow_fallback
    model = load_model(resolved_model_path, allow_fallback=fallback_enabled)
    required_features = load_feature_names(resolved_schema_path, model)
    request_feature_names = [name for name in required_features if name != "cycle"]
    model_metadata = getattr(model, "metadata", {}) or {}
    model_version = str(model_metadata.get("model_version") or metadata.version)
    model_source = "local_pickle" if resolved_model_path.exists() else "fallback"
    monitor = PredictionMonitor(resolved_monitor_path)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ready" if model_source != "fallback" else "degraded",
            "model_loaded": True,
            "model_source": model_source,
            "model_name": metadata.name,
            "model_version": model_version,
            "model_uri": resolve_model_uri(metadata),
            "model_path": resolved_model_path.as_posix(),
            "feature_count": len(required_features),
            "request_feature_count": len(request_feature_names),
            "mlflow_tracking_uri": os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"),
            "monitoring_log_path": resolved_monitor_path.as_posix(),
        }

    @app.post("/predict")
    def predict(payload: PredictionRequest) -> dict[str, float | str]:
        started = time.perf_counter()
        expected = set(request_feature_names)
        received = set(payload.features)
        missing = sorted(expected - received)
        extra = sorted(received - expected)
        if missing or extra:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Prediction features do not match the trained model schema.",
                    "missing_features": missing,
                    "unknown_features": extra,
                },
            )
        features = dict(payload.features)
        features["cycle"] = float(payload.cycle)
        try:
            rul = model.predict_one(features)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        latency_ms = (time.perf_counter() - started) * 1000
        response = build_prediction_response(
            engine_id=payload.engine_id,
            remaining_useful_life=rul,
            model_version=model_version,
            latency_ms=latency_ms,
        )
        monitor.record_prediction(**response)
        return response

    return app


app = create_app()
