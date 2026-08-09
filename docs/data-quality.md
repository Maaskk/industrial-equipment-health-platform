# Data Quality

Quality checks run after dlt ingestion and dbt transformation. A failing dbt command stops the Dagster job and `training-init`.

## Implemented checks

`dbt_project/models/schema.yml` defines 11 tests:

| Model | Checks |
|---|---|
| `stg_sensor_readings` | non-null engine ID and cycle |
| `stg_rul_labels` | non-null and unique engine ID |
| `fct_equipment_health_features` | non-null engine ID, cycle transform, age bucket, split, and subset; accepted values for age bucket and split |

Repository tests also verify:

- raw, staging, and mart tables exist and contain rows
- the mart grain is unique by engine and cycle
- split and age categories are valid
- dlt state is checkout-local or container-local
- DuckDB parent directories are created explicitly
- the NASA archive matches the recorded SHA-256 checksum

The project does not claim sensor range tests, automatic imputation, anomaly flags, `dbt_expectations`, Slack alerts, or freshness alerts because those controls are not implemented.

## Commands

```bash
python scripts/download_data.py
python orchestration/run_local.py
python -m pytest tests/test_dataops.py
```

CI assigns empty temporary directories to `CMAPSS_DATA_DIR`, `DUCKDB_PATH`, `DBT_DUCKDB_PATH`, and `DLT_DATA_DIR` before it runs download, dlt, dbt, and the contracts. This prevents state from another checkout from satisfying the job.
