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

Every successful training run creates a real registered model version and moves the alias:

```bash
MlflowClient().set_registered_model_alias(model_name, "champion", version)
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
