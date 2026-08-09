import json
import os
import time
from pathlib import Path
from typing import Any

from industrial_health.api.contracts import build_prediction_response, build_service_info
from industrial_health.api.data_service import (
    CycleNotFoundError,
    DatasetUnavailableError,
    EngineDataService,
    EngineNotFoundError,
    InsufficientHistoryError,
)
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


def read_feature_schema(schema_path: Path) -> list[str]:
    if not schema_path.exists():
        raise RuntimeError(f"Missing feature schema at {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    required = schema.get("required")
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise RuntimeError(f"Invalid feature schema at {schema_path}")
    return required


def resolve_duckdb_path() -> Path:
    configured = os.getenv("DUCKDB_PATH")
    if configured:
        return Path(configured)
    candidates = [Path("warehouse/cmapss_ingestion.duckdb"), Path("cmapss_ingestion.duckdb")]
    return next((path for path in candidates if path.exists()), candidates[0])


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

    from fastapi import FastAPI, HTTPException, Query
    from pydantic import BaseModel, Field

    class PredictionRequest(BaseModel):
        engine_id: str = Field(..., examples=["engine_001"])
        cycle: int = Field(..., ge=0, examples=[120])
        features: dict[str, float] = Field(default_factory=dict)

    class ReplayRequest(BaseModel):
        mode: str = Field(default="operations", pattern="^(operations|evaluation)$")

    class BatchRequest(BaseModel):
        csv_text: str = Field(..., min_length=1)

    class MaintenanceRequest(BaseModel):
        predicted_rul: float = Field(..., ge=0)
        average_cycles_per_day: float = Field(..., gt=0)
        safety_margin_cycles: float = Field(..., ge=0)

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
    configured_source = os.getenv("MODEL_SOURCE", "local").lower()
    registry_uri = resolve_model_uri(metadata) if configured_source == "mlflow" else None
    schema_features = read_feature_schema(resolved_schema_path) if registry_uri else None
    model = load_model(
        resolved_model_path,
        model_uri=registry_uri,
        allow_fallback=fallback_enabled,
        feature_names=schema_features,
    )
    required_features = load_feature_names(resolved_schema_path, model)
    request_feature_names = [name for name in required_features if name != "cycle"]
    model_metadata = getattr(model, "metadata", {}) or {}
    if registry_uri and metadata.alias:
        from mlflow import MlflowClient

        model_version = str(
            MlflowClient().get_model_version_by_alias(metadata.name, metadata.alias).version
        )
    else:
        model_version = str(model_metadata.get("model_version") or metadata.version)
    model_source = "mlflow_registry" if registry_uri else ("local_pickle" if resolved_model_path.exists() else "fallback")
    monitor = PredictionMonitor(resolved_monitor_path)
    data_service = EngineDataService(
        db_path=resolve_duckdb_path(),
        model=model,
        model_version=model_version,
        monitor=monitor,
        metrics_path=Path(os.getenv("MODEL_METRICS_PATH", "models/latest/metrics.json")),
        drift_path=Path(os.getenv("DRIFT_REPORT_PATH", "reports/monitoring/drift_report.json")),
    )
    app.state.data_service = data_service

    def data_error(exc: Exception) -> HTTPException:
        if isinstance(exc, (EngineNotFoundError, CycleNotFoundError)):
            return HTTPException(status_code=404, detail=str(exc))
        if isinstance(exc, (InsufficientHistoryError, ValueError)):
            return HTTPException(status_code=422, detail=str(exc))
        return HTTPException(status_code=503, detail=str(exc))

    @app.get("/", include_in_schema=False)
    def service_info() -> dict[str, str]:
        return build_service_info()

    @app.get("/demo-payload")
    def demo_payload() -> dict[str, object]:
        path = Path(os.getenv("DEMO_PAYLOAD_PATH", "demo/predict_sample.json"))
        if not path.exists():
            raise HTTPException(status_code=503, detail="Demo payload is not available")
        return json.loads(path.read_text(encoding="utf-8"))

    @app.get("/predictions/recent")
    def recent_predictions(limit: int = 12) -> list[dict[str, object]]:
        bounded_limit = max(1, min(limit, 50))
        if not resolved_monitor_path.exists():
            return []
        lines = resolved_monitor_path.read_text(encoding="utf-8").splitlines()[-bounded_limit:]
        return [json.loads(line) for line in lines if line.strip()]

    @app.get("/api/fleet/summary")
    def fleet_summary() -> dict[str, object]:
        try:
            return data_service.fleet_summary()
        except DatasetUnavailableError as exc:
            raise data_error(exc) from exc

    @app.get("/api/fleet/engines")
    def fleet_engines(
        subset: str | None = None,
        risk: str | None = None,
        search: str | None = None,
        sort: str = Query(default="rul", pattern="^(rul|engine|cycle)$"),
    ) -> list[dict[str, object]]:
        try:
            rows = data_service.fleet()
        except DatasetUnavailableError as exc:
            raise data_error(exc) from exc
        if subset:
            rows = [row for row in rows if row["subset"] == subset.upper()]
        if risk:
            rows = [row for row in rows if row["risk_level"] == risk.lower()]
        if search:
            rows = [row for row in rows if search.upper() in str(row["engine_id"]).upper()]
        key = {
            "rul": lambda row: float(row["remaining_useful_life"]),
            "engine": lambda row: str(row["engine_id"]),
            "cycle": lambda row: int(row["latest_cycle"]),
        }[sort]
        return sorted(rows, key=key)

    @app.get("/api/engines")
    def engines(subset: str | None = None) -> list[dict[str, object]]:
        try:
            return data_service.engines(subset)
        except (DatasetUnavailableError, ValueError) as exc:
            raise data_error(exc) from exc

    @app.get("/api/engines/{engine_id}")
    def engine_detail(
        engine_id: str, cycle: int | None = None, mode: str = "operations"
    ) -> dict[str, object]:
        try:
            return data_service.engine_detail(
                engine_id, cycle, evaluation=mode == "evaluation"
            )
        except (
            DatasetUnavailableError,
            EngineNotFoundError,
            CycleNotFoundError,
            InsufficientHistoryError,
            ValueError,
        ) as exc:
            raise data_error(exc) from exc

    @app.get("/api/engines/{engine_id}/cycles")
    def engine_cycles(engine_id: str) -> dict[str, object]:
        try:
            return data_service.cycles(engine_id)
        except (DatasetUnavailableError, EngineNotFoundError) as exc:
            raise data_error(exc) from exc

    @app.get("/api/engines/{engine_id}/cycle/{cycle}")
    def engine_cycle(
        engine_id: str,
        cycle: int,
        sensors: str = "sensor_2,sensor_3,sensor_11",
        normalized: bool = False,
    ) -> dict[str, object]:
        try:
            return data_service.sensor_series(
                engine_id,
                cycle,
                [value.strip() for value in sensors.split(",")],
                normalized,
            )
        except (
            DatasetUnavailableError,
            EngineNotFoundError,
            CycleNotFoundError,
        ) as exc:
            raise data_error(exc) from exc

    @app.post("/api/engines/{engine_id}/cycle/{cycle}/predict")
    def replay_prediction(
        engine_id: str, cycle: int, payload: ReplayRequest
    ) -> dict[str, object]:
        try:
            return data_service.predict_cycle(
                engine_id, cycle, include_truth=payload.mode == "evaluation"
            )
        except (
            DatasetUnavailableError,
            EngineNotFoundError,
            CycleNotFoundError,
            InsufficientHistoryError,
            ValueError,
        ) as exc:
            raise data_error(exc) from exc

    @app.post("/api/predict/batch")
    def batch_prediction(payload: BatchRequest) -> dict[str, object]:
        try:
            rows, csv_output = data_service.score_csv(payload.csv_text)
        except ValueError as exc:
            raise data_error(exc) from exc
        return {"rows": rows, "csv": csv_output}

    @app.get("/api/model/info")
    def model_info() -> dict[str, object]:
        return data_service.model_info()

    @app.get("/api/platform/status")
    def platform_status() -> dict[str, object]:
        try:
            return data_service.platform_status()
        except DatasetUnavailableError as exc:
            raise data_error(exc) from exc

    @app.get("/api/monitoring/summary")
    def monitoring_summary() -> dict[str, object]:
        return data_service.monitoring_summary()

    @app.get("/api/drift/latest")
    def latest_drift() -> dict[str, object]:
        summary = data_service.monitoring_summary()
        return {"drift": summary["drift"]}

    @app.post("/api/maintenance/plan")
    def maintenance_plan(payload: MaintenanceRequest) -> dict[str, object]:
        service_cycles = max(0.0, payload.predicted_rul - payload.safety_margin_cycles)
        days = service_cycles / payload.average_cycles_per_day
        priority = "high" if service_cycles <= 15 else "medium" if service_cycles <= 45 else "low"
        return {
            "maximum_cycles_before_service": round(service_cycles, 1),
            "estimated_operating_days": round(days, 1),
            "priority": priority,
            "recommendation": (
                "Plan service immediately"
                if priority == "high"
                else "Reserve an inspection window"
                if priority == "medium"
                else "Continue operation and monitor"
            ),
            "utilization_assumption": payload.average_cycles_per_day,
        }

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
