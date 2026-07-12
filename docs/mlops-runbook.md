# MLOps Runbook

Owner: `Maaskk`

Branch: `owner/Maaskk`

## Local API

```bash
PYTHONPATH=src python scripts/run_api.py
```

Health check:

```bash
curl http://localhost:8000/health
```

Prediction with the generated schema-valid payload:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  --data @demo/predict_sample.json
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
models:/industrial-equipment-health-model@champion
```

Training creates a registered model version and updates the `champion` alias. The Docker API loads that alias directly from MLflow.

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

## Readiness Report

```bash
PYTHONPATH=src python scripts/check_readiness.py
```

The report is written to:

```text
reports/readiness/maaskk-readiness.json
```
