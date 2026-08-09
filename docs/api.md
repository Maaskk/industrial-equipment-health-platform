# API Demo Guide

The FastAPI service serves the existing dashboard and the trained NASA C-MAPSS Remaining Useful Life model. Production is available at `http://exp.s3.fsbm.ma:3402/`.

## Startup Contract

By default the API refuses to start unless `models/latest/model.pkl` exists. This prevents a silent fake demo. The deterministic fallback is allowed only for tests with:

```bash
ALLOW_FALLBACK_MODEL=true
```

For the real local demo, generate the model first:

```bash
PYTHONPATH=src python scripts/train_model.py --download
uvicorn industrial_health.api.app:app --host 0.0.0.0 --port 8000
```

## Health

```bash
curl http://localhost:8000/health
```

Expected fields:

- `status`: `ready` when a real local model is loaded.
- `model_loaded`: `true` after startup succeeds.
- `model_source`: `mlflow_registry` in Komodo, `local_pickle` for a local trained artifact, and `fallback` only in explicit tests.
- `model_version`: model version served by the API.
- `feature_count`: number of features expected by the trained model.
- `mlflow_tracking_uri`: tracking backend used by training.
- `monitoring_log_path`: JSONL prediction log location.
- `release_sha`: deployed Git commit.
- `release_tag`: deployed immutable tag.

Production acceptance requires `model_source: mlflow_registry`; the local pickle path is used only for local reproduction and tests.

## Prediction

Use the generated sample payload:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  --data @demo/predict_sample.json
```

The API validates the request against `models/latest/feature_schema.json`. `cycle` is sent as a top-level field. All other trained features must be present in `features`, and unknown fields are rejected with HTTP `422`.

Successful response:

```json
{
  "engine_id": "FD004_204",
  "remaining_useful_life": 123.66,
  "risk_level": "low",
  "model_version": "1",
  "latency_ms": 8.4
}
```

Each prediction is appended to `logs/prediction_logs.jsonl` for monitoring proof.

## Engineering Console API

The web console uses the same service and model as the public prediction contract. It
does not generate random telemetry or client-side predictions.

| Endpoint | Purpose |
|---|---|
| `GET /api/fleet/summary` | Fleet risk counts and aggregate predicted RUL |
| `GET /api/fleet/engines` | Sortable engine-level predictions at each latest cycle |
| `GET /api/engines?subset=FD004` | Engines and cycle limits for one subset |
| `GET /api/engines/{id}/cycles` | Replay boundaries |
| `GET /api/engines/{id}/cycle/{cycle}` | Historical sensor series through a selected cycle |
| `POST /api/engines/{id}/cycle/{cycle}/predict` | Real operations/evaluation prediction |
| `POST /api/predict/batch` | Validate and score uploaded C-MAPSS-style CSV data |
| `GET /api/model/info` | Model identity and held-out evaluation evidence |
| `GET /api/platform/status` | DataOps/MLOps artifact evidence |
| `GET /api/monitoring/summary` | Prediction volume, latency, risk, change, and drift evidence |
| `POST /api/maintenance/plan` | Maintenance recommendation from a real prediction |

Engine replay requires at least five observed cycles because the trained feature schema
contains five-cycle rolling statistics and slopes. `mode=operations` never returns
future truth. `mode=evaluation` may return `actual_rul` and `prediction_error` because
the C-MAPSS test labels are available for offline assessment.

The 3D turbofan is a locally bundled, interactive Three.js cutaway visualization. It
provides component focus controls, an exploded view, animated airflow and rotating stages,
sensor beacons, and risk-linked lighting. It is not a physical simulation or certification
model; inference remains dataset-backed even when WebGL is unavailable.
