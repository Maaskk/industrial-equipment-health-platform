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
export MODEL_VERSION=1
export MLFLOW_TRACKING_URI=http://localhost:5000
```

The API resolves the registered model URI as:

```text
models:/industrial-equipment-health-model/1
```

If a stage is used:

```bash
export MODEL_STAGE=Production
```

then the URI becomes:

```text
models:/industrial-equipment-health-model/Production
```

## Artifact Contract From ML Team

Mouhcine provides:

```text
models/latest/model.pkl
models/latest/feature_schema.json
models/latest/metrics.json
```

Ossama registers the model and serves it. Until the model artifact exists, the API uses a deterministic fallback model so the integration demo can still run.

## Required MLflow Evidence

The final presentation should show:

- experiment name
- run parameters
- metrics
- model artifact
- registered model version
- selected model version used by the API

