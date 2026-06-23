# MLOps Runbook

Owner: `Maaskk`

Branch: `owner/Maaskk-mlops-integration`

## Local API

```bash
PYTHONPATH=src python scripts/run_api.py
```

Health check:

```bash
curl http://localhost:8000/health
```

Prediction:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"engine_id":"engine_001","cycle":120,"features":{"sensor_1":518.67}}'
```

## Docker

```bash
docker compose up --build
```

Services:

- API: http://localhost:8000
- MLflow: http://localhost:5000

## Model Registry Contract

The API resolves models using:

```text
models:/industrial-equipment-health-model/<MODEL_VERSION>
```

or, when `MODEL_STAGE` is set:

```text
models:/industrial-equipment-health-model/<MODEL_STAGE>
```

## Monitoring

Prediction telemetry is stored in:

```text
logs/prediction_logs.jsonl
```

Each line contains:

- `timestamp_utc`
- `engine_id`
- `remaining_useful_life`
- `risk_level`
- `model_version`
- `latency_ms`

This is intentionally simple for the course demo. It can later be replaced with Prometheus, Grafana, Evidently, or another observability stack.

