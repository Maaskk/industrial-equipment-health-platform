# Team Integration Contracts

The team works independently on separate branches. Everyone must respect these contracts so Ossama can merge branches cleanly into `main`.

## Branch Rule

Each member works only in their branch:

```text
owner/Maaskk-mlops-integration
feature/mohamed-kar1-dataops-infra
feature/HamzaElhaddaji-quality-docs
feature/Mouhcine005-ml-modeling
feature/HajarEnnajdy-api-demo
feature/ilyass-analytics-eda
feature/Adonis-I-agile-release
```

## Folder Ownership

| Owner | Primary folders |
|---|---|
| Maaskk | `src/industrial_health/mlops/`, `src/industrial_health/api/`, `docker/`, `.github/workflows/`, `docs/monitoring.md` |
| mohamed-kar1 | `src/industrial_health/ingestion/`, `orchestration/`, `dlt/`, `duckdb/` |
| HamzaElhaddaji | `contracts/`, `dbt/`, `docs/data-quality.md`, `tests/data_quality/` |
| Mouhcine005 | `src/industrial_health/modeling/`, `notebooks/modeling/`, `reports/model_metrics/` |
| HajarEnnajdy | `src/industrial_health/api/schemas.py`, `demo/`, `docs/api.md` |
| ilyass | `notebooks/eda/`, `reports/figures/`, `docs/business-analysis.md` |
| Adonis-I | `agile/`, `docs/final-report/`, `presentation/` |

## Shared Contracts

### Feature Table Contract

The ML model expects a feature table with:

```text
engine_id: string or integer
cycle: integer
setting_1, setting_2, setting_3: numeric
sensor_1 ... sensor_21: numeric
rul: numeric target, training only
```

Optional engineered features:

```text
sensor_*_rolling_mean_5
sensor_*_rolling_std_5
cycle_norm
engine_age_bucket
```

### Model Artifact Contract

Mouhcine provides:

```text
models/latest/model.pkl
models/latest/feature_schema.json
models/latest/metrics.json
```

Ossama registers this model in MLflow and serves it through FastAPI.

### API Contract

Hajar and Ossama keep this stable:

```http
GET /health
POST /predict
```

`POST /predict` input:

```json
{
  "engine_id": "engine_001",
  "cycle": 120,
  "features": {
    "setting_1": 0.0,
    "sensor_1": 518.67
  }
}
```

`POST /predict` output:

```json
{
  "engine_id": "engine_001",
  "remaining_useful_life": 42.0,
  "risk_level": "medium",
  "model_version": "1"
}
```

## Pull Request Checklist

Every pull request must include:

- Branch name.
- Owner name.
- Summary of files changed.
- Commands run.
- Screenshots/logs if relevant.
- Any contract changed.

If a contract changes, tag Ossama before merge.
