# Architecture

## Modules

| Module | Owner | Purpose |
|---|---|---|
| Ingestion | Mohamed | Load raw sensor data using dlt into DuckDB |
| Warehouse | Mohamed and Hamza | Store raw, staging, marts, and feature tables |
| Transformations | Mohamed and Hamza | Build dbt models and enforce quality checks |
| Orchestration | Mohamed and Ossama | Run ingestion, transformation, training, and validation with Dagster |
| ML Training | Mouhcine | Train, evaluate, and package scikit-learn models |
| Tracking | Ossama and Mouhcine | Track experiments and promote models through MLflow |
| Serving | Ossama and Hajar | Serve predictions through FastAPI |
| Monitoring | Ossama and Hamza | Track service health, latency, data drift, and model metrics |
| Analytics | Ilyass | Prepare EDA, KPIs, charts, and evidence for the report |
| Agile and Release | Akram | Maintain backlog, sprint ceremonies, and final delivery checklist |

## Data Layers

```text
raw_sensor_readings
  -> stg_sensor_readings
  -> int_engine_lifecycle_windows
  -> fct_equipment_health_features
  -> model_training_dataset
  -> prediction_logs
```

## API Contract

### GET /health

Returns service status, model version, and dependency status.

### POST /predict

Input:

```json
{
  "engine_id": "engine_001",
  "cycle": 135,
  "sensors": {
    "sensor_1": 518.67,
    "sensor_2": 641.82
  }
}
```

Output:

```json
{
  "engine_id": "engine_001",
  "risk_level": "high",
  "remaining_useful_life": 24.7,
  "model_version": "1"
}
```

