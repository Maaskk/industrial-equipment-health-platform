# API Demo Guide

The FastAPI service serves the trained NASA C-MAPSS Remaining Useful Life model.

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
- `model_source`: `local_pickle` for the trained artifact, `fallback` only in explicit tests.
- `model_version`: model version served by the API.
- `feature_count`: number of features expected by the trained model.
- `mlflow_tracking_uri`: tracking backend used by training.
- `monitoring_log_path`: JSONL prediction log location.

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
