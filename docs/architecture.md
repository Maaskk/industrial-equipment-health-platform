# Production Architecture

The university deployment is the primary application. No external frontend host is required.

```text
Browser
  -> exp.s3.fsbm.ma:3402
     -> FastAPI dashboard and same-origin API
        -> MLflow model registry
        -> DuckDB feature mart
        -> persistent prediction log

GitHub release
  -> CI
  -> protected production approval
  -> Komodo Stack on vh3
     -> mlflow
     -> training-init
     -> api
     -> dagster-webserver
     -> dagster-daemon
     -> ops-gateway
```

## Runtime services

| Service | Purpose | State after deployment |
|---|---|---|
| `mlflow` | Experiment tracking, artifacts, model registry, champion alias | long-running |
| `training-init` | Download, dlt, dbt, tests, training, registration, drift report | exits successfully |
| `api` | Existing dashboard, FastAPI routes, MLflow champion inference | long-running |
| `dagster-webserver` | Asset, job, run, and schedule interface | long-running |
| `dagster-daemon` | Executes the enabled daily schedule | long-running |
| `ops-gateway` | Authenticated access to the MLflow and Dagster consoles | long-running |

Named volumes retain NASA data, DuckDB, models, reports, Dagster state, MLflow state, and prediction logs. `deploy/compose.production.yml` is the Compose definition used by the Komodo Stack.

## Browser contract

The page at `/` uses relative URLs for product requests. The important routes are `/health`, `/predict`, `/docs`, and `/api/*`. MLflow and Dagster links are configured with `MLFLOW_PUBLIC_URL` and `DAGSTER_PUBLIC_URL`.

## Model contract

Production sets `MODEL_SOURCE=mlflow`. The API resolves `models:/industrial-equipment-health-model@champion`, reports the resolved version through `/health`, and refuses to start if the registry model cannot load. The local pickle is a reproducibility artifact, not the production source.

## Scope

NASA C-MAPSS contains simulated degradation trajectories. Engine Replay replays those stored trajectories. The Three.js turbine is an explanatory sensor visualization, not live telemetry or a physical turbine simulation.
