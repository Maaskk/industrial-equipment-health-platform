# MLflow Model Registry

Owner: `Maaskk`

## Registry Naming

Use this model name:

```text
industrial-equipment-health-model
```

Use these environment variables:

```bash
export MODEL_NAME=industrial-equipment-health-model
export MODEL_ALIAS=champion
export MLFLOW_TRACKING_URI=http://localhost:5000
```

The API resolves the registered model URI as:

```text
models:/industrial-equipment-health-model@champion
```

Every successful training run creates a registered candidate. The promotion gate
resolves the current champion and compares `standard_final_mae` and
`standard_final_rmse`. The candidate receives the alias only when both metrics
are no worse. The first candidate becomes champion when no alias exists. Missing
champion metrics block the promotion.

The decision is stored in MLflow tags and in:

```text
reports/model_metrics/promotion_decision.json
```

## Artifact Contract From ML Team

Mouhcine provides:

```text
models/latest/model.pkl
models/latest/feature_schema.json
models/latest/metrics.json
```

The training pipeline writes these recovery artifacts and registers the same trained estimator in MLflow. In Docker, FastAPI loads the `champion` alias from the Registry. The deterministic fallback is disabled unless explicitly enabled for tests.

## Required MLflow Evidence

The final presentation should show:

- experiment name
- run parameters
- metrics
- model artifact
- registered model version
- selected model version used by the API
- promotion decision and previous champion
