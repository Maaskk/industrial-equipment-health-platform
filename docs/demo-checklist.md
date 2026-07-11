# Final Demo Checklist

Owner: `Maaskk`

## Before the Demo

- `main` has the final merged code.
- Docker builds successfully.
- MLflow opens locally.
- API health endpoint returns `status: ready` and `model_source: mlflow_registry`.
- Prediction endpoint returns RUL, risk level, model version, and latency.
- Prediction logs are generated.
- At least one drift example is ready.

## Demo Flow

1. Show repository structure and team branches.
2. Show data source and NASA dataset citation.
3. Run or explain the DataOps pipeline.
4. Show MLflow experiments and registered model.
5. Start the API.
6. Call `GET /health`.
7. Call `POST /predict`.
8. Show `logs/prediction_logs.jsonl`.
9. Show simple drift report.
10. Explain how each teammate's branch merged into the final product.

## Commands

```bash
docker compose up --build
```

```bash
curl http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  --data @demo/predict_sample.json
```

Run the smoke script:

```bash
PYTHONPATH=src python scripts/smoke_predict.py
```

Generate readiness evidence:

```bash
PYTHONPATH=src python scripts/check_readiness.py
```
