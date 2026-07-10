# Industrial Equipment Health Platform Final Report

## Executive Summary

This project implements a local MLOps/DataOps platform for predictive maintenance using the NASA C-MAPSS turbofan degradation dataset. The platform ingests raw files, stores them in DuckDB, transforms them with dbt, orchestrates assets with Dagster, trains a Remaining Useful Life model with scikit-learn, logs training evidence to MLflow, serves predictions through FastAPI, and records prediction telemetry for monitoring.

## Dataset

Primary source: NASA Turbofan Engine Degradation Simulation Data Set.

The final training run used all four subsets:

- FD001
- FD002
- FD003
- FD004

Raw dataset size used by training:

- Training rows: 160,359
- Test rows: 104,897
- Training engines: 709
- Test engines: 707

Raw data is downloaded by `scripts/download_data.py` and is not committed to git.

## DataOps Pipeline

The local DataOps path is:

```text
NASA C-MAPSS files -> dlt -> DuckDB raw schema -> dbt staging -> dbt marts -> Dagster assets
```

Local verification command:

```bash
PYTHONPATH=src python orchestration/run_local.py
```

Verified locally:

- dlt loaded the full FD001-FD004 raw data.
- dbt created 3 models.
- dbt passed 8 data tests.
- pytest DataOps checks passed: 11 tests.

## Modeling

Final model: `HistGradientBoostingRegressor`

Feature engineering:

- operational settings
- 21 raw sensor channels
- 5-cycle rolling means
- 5-cycle rolling standard deviations
- 5-cycle rolling slopes
- subset identifier
- cycle

Evaluation approach:

- standard final-observed-cycle test metric per engine
- online row-level metric as secondary evidence
- mean baseline
- cycle-only Ridge baseline
- raw-feature Ridge baseline
- raw-feature RandomForest baseline
- final gradient boosting model

Final standard test metrics:

- MAE: 12.5568 cycles
- RMSE: 16.9251 cycles
- NASA asymmetric score: 4466.3383

Training proof:

- `reports/model_metrics/final_evaluation.json`
- `reports/model_metrics/final_evaluation.md`
- `reports/model_metrics/figures/final_model_comparison.png`
- `notebooks/training_executed.ipynb`

## Serving

FastAPI endpoints:

- `GET /health`
- `POST /predict`

The API loads `models/latest/model.pkl` and validates requests against `models/latest/feature_schema.json`. A missing model raises an error by default; fallback prediction is test-only behind `ALLOW_FALLBACK_MODEL=true`.

Demo payload:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  --data @demo/predict_sample.json
```

## Docker Reproducibility

Professor-approved local deployment command:

```bash
docker compose up --build
```

Services:

- `mlflow`
- `training-init`
- `api`
- `dagster-webserver`
- `dagster-daemon`

## Monitoring

Prediction telemetry is appended to:

```text
logs/prediction_logs.jsonl
```

Drift report command:

```bash
PYTHONPATH=src python scripts/generate_drift_report.py
```

Output:

```text
reports/monitoring/drift_report.json
```

## Limitations

- NASA C-MAPSS is simulated, not live factory telemetry.
- The risk level is threshold-based from predicted RUL, not a separate calibrated classifier.
- Local Docker Compose replaces Oracle Cloud because the professor explicitly allowed local development first.
- The final branch must still be merged into `main` after review.
