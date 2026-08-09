# Data Lineage

```text
NASA C-MAPSS archive (verified SHA-256)
  -> dlt resources
     -> raw.raw_sensor_readings       265,256 rows
     -> raw.raw_rul_labels                707 rows
  -> dbt
     -> staging.stg_sensor_readings   265,256 rows
     -> staging.stg_rul_labels            707 rows
     -> marts.fct_equipment_health_features 265,256 rows
  -> Python point-in-time feature generation
  -> HistGradientBoostingRegressor
  -> MLflow run, artifact, registered version, champion alias
  -> FastAPI prediction and JSONL monitoring records
```

The counts above come from the full FD001, FD002, FD003, and FD004 warehouse used for final local evidence.

## Actual dbt models

The project has exactly three dbt models:

1. `stg_sensor_readings` filters invalid identifiers from dlt sensor rows.
2. `stg_rul_labels` prepares final RUL labels.
3. `fct_equipment_health_features` adds split, subset, cycle age, and selected causal five-cycle rolling statistics.

## Training features

`scripts/train_model.py` reads the DuckDB mart, constructs five-cycle mean, standard deviation, and slope features for all 21 sensors, drops incomplete warm-up rows, and trains with 89 features. Every rolling value uses only the current and preceding cycles.

Full training evidence:

- 160,359 raw training rows and 104,897 raw test rows
- 709 training engines and 707 test engines
- 157,523 training rows after rolling warm-up
- 102,069 online test rows after rolling warm-up
- 707 engines in the standard final-cycle evaluation
