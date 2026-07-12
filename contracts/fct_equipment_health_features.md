# Data Contract: Equipment Health Features

## Contract

| Property | Value |
|---|---|
| Contract ID | `DC-003-FEATURES` |
| Owners | Hamza Elhaddaji and Mouhcine |
| Status | Approved and enforced |
| Last updated | 2026-07-11 |
| Upstream | `staging.stg_sensor_readings` |
| Storage | `marts.fct_equipment_health_features` in DuckDB |
| Downstream | `scripts/train_model.py` |

The mart is the reviewed interface between DataOps and model training. Training reads this table directly when `TRAIN_SOURCE=duckdb`, which is the default and the Docker configuration.

## Grain And Required Columns

One row represents one observed cycle for one engine trajectory.

- Identity: `engine_id`, `cycle`, `source_file`, `split`, `subset_id`
- Operating settings: `setting_1` through `setting_3`
- Sensors: `sensor_1` through `sensor_21`
- Point-in-time-safe features: `cycle_log1p`, `engine_age_bucket`
- Causal windows: selected `sensor_*_rolling_mean_5` and `sensor_*_rolling_std_5`

The target is intentionally not stored as a model feature. Training RUL is constructed from completed training trajectories; test RUL is constructed from `staging.stg_rul_labels`. Neither target nor an engine-final-cycle value enters the predictor matrix.

## Leakage Policy

Every model input must be available at the current cycle. Features that divide by, aggregate over, or otherwise reveal the final cycle of an engine are forbidden. In particular, the former `cycle_norm = cycle / max_cycle` feature was removed because it had different train and serving semantics.

Rolling features use `rows between 4 preceding and current row`. The Python model pipeline also creates causal rolling means, standard deviations, and slopes from the curated mart.

## Quality Rules

- `engine_id`, `cycle`, `split`, `subset_id`, and `cycle_log1p` are non-null.
- `split` is exactly `train` or `test`.
- `engine_age_bucket` is exactly `early`, `middle`, or `late`.
- Each source trajectory retains all 21 numeric sensors and three settings.
- The full four-subset mart contains 265,256 rows before rolling warm-up.
- dbt tests and `tests/test_dataops.py` must pass before model training.

## Handoff

```text
dlt raw tables
  -> dbt staging
  -> marts.fct_equipment_health_features
  -> scripts/train_model.py --source duckdb
  -> MLflow run and registered model version
  -> FastAPI loads models:/industrial-equipment-health-model@champion
```

The generated serving schema at `models/latest/feature_schema.json` is the final API-to-model contract.
