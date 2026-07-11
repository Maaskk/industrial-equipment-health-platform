# DataOps Infrastructure — Mohamed Kar1

Branch: `feature/mohamed-kar1-dataops-infra`

## Overview

This module implements the full DataOps foundation for the industrial equipment health platform:
- **dlt** — raw data ingestion from NASA C-MAPSS files into DuckDB
- **DuckDB** — local analytical warehouse (raw → staging → marts)
- **dbt** — transformations and data quality tests (staging + marts models)
- **Dagster** — pipeline orchestration with assets, jobs, and daily schedule

---

## Stack

| Tool | Version | Role |
|------|---------|------|
| dlt | 1.28+ | Ingestion |
| DuckDB | 1.5+ | Local warehouse |
| dbt-core / dbt-duckdb | 1.11+ / 1.10+ | Transformations & data quality |
| Dagster | 1.13+ | Orchestration |
| Python | 3.11 | Runtime |

All four tools run in a **single Python virtual environment** (`venv/`), built from `requirements.txt` plus `dbt-core` / `dbt-duckdb`.

---

## Folder Structure

```
industrial-equipment-health-platform/
├── src/industrial_health/
│   └── ingestion/
│       ├── __init__.py
│       └── dlt_pipeline.py
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── macros/
│   │   └── generate_schema_name.sql
│   └── models/
│       ├── schema.yml
│       ├── staging/
│       │   ├── sources.yml
│       │   ├── stg_sensor_readings.sql
│       │   └── stg_rul_labels.sql
│       └── marts/
│           └── fct_equipment_health_features.sql
├── orchestration/
│   ├── dagster_assets.py
│   └── run_local.py
├── duckdb/
└── data/
    └── raw/   ← NASA C-MAPSS files (NOT committed)
```

---

## Dataset

Download NASA C-MAPSS from:
https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/

Place the following files in `data/raw/`:

```
train_FD001.txt  train_FD002.txt  train_FD003.txt  train_FD004.txt
test_FD001.txt   test_FD002.txt   test_FD003.txt   test_FD004.txt
RUL_FD001.txt    RUL_FD002.txt    RUL_FD003.txt    RUL_FD004.txt
```

> Data files must NOT be committed to git.

---

## Setup

A single virtual environment is used for the whole pipeline:

```bash
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install dbt-core dbt-duckdb
```

```bash
git clone https://github.com/Maaskk/industrial-equipment-health-platform.git
cd industrial-equipment-health-platform
git checkout feature/mohamed-kar1-dataops-infra
```

---

## Run the Pipeline

### Option A — Local script (no UI)

```bash
python orchestration/run_local.py
```

Expected output:

```
=== Step 1: Ingestion dlt ===
Pipeline cmapss_ingestion load step completed in ~50 seconds
Load package ... is LOADED and contains no failed jobs

=== Step 2: dbt run (staging + marts) ===
Done. PASS=3 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=3

=== Step 3: dbt test ===
Done. PASS=8 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=8

=== Done. Feature table ready for Mouhcine. ===
```

### Option B — dbt directly

```bash
set DBT_DUCKDB_PATH=<absolute path to cmapss_ingestion.duckdb>
cd dbt_project
dbt run
dbt test
```

### Option C — Dagster UI

```bash
python -m dagster dev -f orchestration/dagster_assets.py
```

Open http://localhost:3000 → Assets → Select all → Materialize selected

---

## Run Tests

```bash
python -m pytest tests/test_dataops.py -v
```

---

## DuckDB Warehouse Structure

| Schema | Table | Produced by | Description |
|--------|-------|-------------|-------------|
| raw | raw_sensor_readings | dlt | Raw sensor data ingested by dlt |
| raw | raw_rul_labels | dlt | Raw RUL labels ingested by dlt |
| staging | stg_sensor_readings | dbt | Cleaned sensor readings (265 256 rows) |
| staging | stg_rul_labels | dbt | Cleaned RUL labels |
| marts | fct_equipment_health_features | dbt | Feature-engineered table for ML |

All transformations between raw, staging, and marts are implemented as dbt models
(`dbt_project/models/staging/`, `dbt_project/models/marts/`), with native dbt tests
acting as the data contract (`not_null`, `unique`, `accepted_values`).

Database file: `cmapss_ingestion.duckdb` (at project root).

---

## Feature Engineering

| Feature | Description |
|---------|-------------|
| `cycle_log1p` | Point-in-time-safe transform of the current cycle |
| `engine_age_bucket` | early / middle / late, based only on the current cycle |
| `sensor_*_rolling_mean_5` | Rolling mean over 5 cycles (sensors 1,2,3,4,7,11,12,15) |
| `sensor_*_rolling_std_5` | Rolling std over 5 cycles (sensors 1,2,3,4,7,11,12,15) |

---

## dbt Data Quality Tests

| Model | Column | Test |
|-------|--------|------|
| stg_sensor_readings | engine_id, cycle | not_null |
| stg_rul_labels | engine_id | not_null, unique |
| fct_equipment_health_features | engine_id, cycle_log1p, split, subset_id | not_null |
| fct_equipment_health_features | engine_age_bucket | not_null, accepted_values (early/middle/late) |

Result: **8/8 tests passing.**

---

## Dagster Assets

| Asset | Description |
|-------|-------------|
| `raw_sensor_data` | dlt ingestion → DuckDB raw schema |
| `dbt_transform` | Runs `dbt run` (staging + marts models) |
| `dbt_test` | Runs `dbt test` (data quality checks) |
| `feature_table_validation` | Validates `staging.stg_sensor_readings` row count |
| `feature_engineering` | Validates `marts.fct_equipment_health_features` row count |
| `model_training` | Executes the real notebook, evaluates the model, and registers it in MLflow |
| `drift_report` | Produces monitoring evidence after model registration |

Schedule: daily at 06:00.
All 7 assets run in one dependency graph; the Docker startup materialization is preserved in shared Dagster storage.

---

## Feature Table Contract (for Mouhcine)

```
DB file  : cmapss_ingestion.duckdb
Schema   : marts
Table    : fct_equipment_health_features
Produced by: dbt (dbt_project/models/marts/fct_equipment_health_features.sql)
Columns  : engine_id, cycle, setting_1..3, sensor_1..21,
           split, subset_id, cycle_log1p, engine_age_bucket,
           sensor_*_rolling_mean_5, sensor_*_rolling_std_5
Rows     : 265 256
```

---

## Acceptance Criteria

| Criteria | Status |
|----------|--------|
| Raw data can be ingested reproducibly | ✅ |
| DuckDB contains raw, staging and marts tables | ✅ |
| Transformations implemented with dbt (not raw SQL) | ✅ |
| dbt data quality tests passing (8/8) | ✅ |
| Dagster can run the full pipeline locally | ✅ |
| Single virtual environment for all 4 tools | ✅ |
| Feature table path documented for Mouhcine | ✅ |
| Commands documented and tested | ✅ |
```
