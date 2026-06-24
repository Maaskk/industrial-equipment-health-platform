# DataOps Infrastructure — Mohamed Kar1

Branch: `feature/mohamed-kar1-dataops-infra`

## Overview

This module implements the full DataOps foundation for the industrial equipment health platform:
- **dlt** — raw data ingestion from NASA C-MAPSS files into DuckDB
- **DuckDB** — local analytical warehouse (raw → staging → marts)
- **Dagster** — pipeline orchestration with assets, jobs, and daily schedule

---

## Stack

| Tool | Version | Role |
|------|---------|------|
| dlt | 1.28+ | Ingestion |
| DuckDB | 1.5+ | Local warehouse |
| Dagster | 1.13+ | Orchestration |
| Python | 3.11+ | Runtime |

---

## Folder Structure

```
industrial-equipment-health-platform/
├── src/industrial_health/
│   └── ingestion/
│       ├── __init__.py
│       └── dlt_pipeline.py
├── orchestration/
│   ├── dagster_assets.py
│   └── run_local.py
├── duckdb/
│   └── duckdb_setup.py
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

```bash
git clone https://github.com/Maaskk/industrial-equipment-health-platform.git
cd industrial-equipment-health-platform
git checkout feature/mohamed-kar1-dataops-infra
pip install dlt[duckdb] duckdb dagster dagster-webserver pandas
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

=== Step 2: DuckDB setup ===
DuckDB warehouse ready at cmapss_ingestion.duckdb
staging.stg_sensor_readings : 265256 lignes

=== Done. Feature table ready for Mouhcine. ===
```

### Option B — Dagster UI

```bash
python -m dagster dev -f orchestration/dagster_assets.py
```

Open http://localhost:3000 → Catalog → Select all → Materialize selected

---

## Run Tests

```bash
python -m pytest tests/test_dataops.py -v
```

Expected: **11 passed**

---

## DuckDB Warehouse Structure

| Schema | Table | Description |
|--------|-------|-------------|
| raw | raw_sensor_readings | Raw sensor data ingested by dlt |
| raw | raw_rul_labels | Raw RUL labels ingested by dlt |
| staging | stg_sensor_readings | Cleaned sensor readings (265 256 rows) |
| staging | stg_rul_labels | Cleaned RUL labels |
| marts | fct_equipment_health_features | Feature-engineered table for ML |

---

## Feature Engineering

| Feature | Description |
|---------|-------------|
| `cycle_norm` | Cycle normalized between 0 and 1 |
| `engine_age_bucket` | young / middle / old |
| `sensor_*_rolling_mean_5` | Rolling mean over 5 cycles (sensors 1,2,3,4,7,11,12,15) |
| `sensor_*_rolling_std_5` | Rolling std over 5 cycles (sensors 1,2,3,4,7,11,12,15) |

---

## Dagster Assets

| Asset | Description |
|-------|-------------|
| `raw_sensor_data` | dlt ingestion → DuckDB raw schema |
| `duckdb_warehouse` | staging + marts + feature engineering |
| `feature_table_validation` | validates staging.stg_sensor_readings row count |
| `feature_engineering` | validates marts.fct_equipment_health_features row count |

Schedule: daily at 06:00.

---

## Feature Table Contract (for Mouhcine)

```
DB file  : cmapss_ingestion.duckdb
Schema   : marts
Table    : fct_equipment_health_features
Columns  : engine_id, cycle, setting_1..3, sensor_1..21,
           cycle_norm, engine_age_bucket,
           sensor_*_rolling_mean_5, sensor_*_rolling_std_5
Rows     : 265 256
```

---

## Acceptance Criteria

| Criteria | Status |
|----------|--------|
| Raw data can be ingested reproducibly | ✅ |
| DuckDB contains raw and staging tables | ✅ |
| Dagster can run the pipeline locally | ✅ |
| Feature table path documented for Mouhcine | ✅ |
| Commands documented and tested | ✅ |
| 11 unit tests passing | ✅ |
