# Data Contract: Equipment Health Features

## 1. Overview

| Property | Value |
|----------|-------|
| **Contract ID** | `DC-003-FEATURES` |
| **Owner** | Hamza Elhaddaji & Mouhcine |
| **Status** | Draft (Sprint 1-2) |
| **Last Updated** | 2024-Q3 |
| **Upstream** | `stg_sensor_readings` |
| **Downstream** | ML Training Pipeline |
| **Storage** | DuckDB (marts schema) |

---

## 2. Purpose

This contract defines the **feature table** used for machine learning model training and inference. It contains engineered features derived from raw sensor data and is the final contract between Data Engineering and ML Engineering.

---

## 3. Table: `fct_equipment_health_features`

### 3.1 Core Schema (Required for Training)

| Column Name | Data Type | Nullable | Source | Description |
|------------|-----------|----------|--------|-------------|
| `feature_id` | VARCHAR(50) | NO | Computed | Unique: `engine_{id}_cycle_{cycle}` |
| `engine_id` | INTEGER | NO | `stg_sensor_readings` | Engine identifier |
| `cycle` | INTEGER | NO | `stg_sensor_readings` | Operating cycle |
| `setting_1` | NUMERIC(10,6) | NO | `stg_sensor_readings` | Engine setting 1 (raw) |
| `setting_2` | NUMERIC(10,6) | NO | `stg_sensor_readings` | Engine setting 2 (raw) |
| `setting_3` | NUMERIC(10,6) | NO | `stg_sensor_readings` | Engine setting 3 (raw) |
| `sensor_1` to `sensor_21` | NUMERIC(10,2) | NO | `stg_sensor_readings` | 21 raw sensor readings |
| **`rul`** | NUMERIC(10,2) | NO | `stg_sensor_readings` | **Target Variable: Remaining Useful Life** |

### 3.2 Engineered Features (Optional)

These features improve model performance and are created if time permits in Sprint 2:

| Column Name | Data Type | Source | Description |
|------------|-----------|--------|-------------|
| `sensor_1_rolling_mean_5` | NUMERIC(10,2) | Computed | 5-cycle rolling mean of sensor 1 |
| `sensor_*_rolling_std_5` | NUMERIC(10,2) | Computed | 5-cycle rolling std of each sensor |
| `cycle_norm` | NUMERIC(10,2) | Computed | Normalized cycle position (0-1 per engine) |
| `engine_age_bucket` | VARCHAR(20) | Computed | Cycle bucket: 'early', 'mid', 'late' |
| `sensor_degradation_rate` | NUMERIC(10,4) | Computed | Rate of change in sensor values |

### 3.3 Metadata Columns

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `dataset_split` | VARCHAR(20) | 'train', 'test', or 'val' |
| `feature_created_at` | TIMESTAMP | When feature row was created |
| `model_version` | VARCHAR(20) | Feature schema version |

---

## 4. Quality Rules & Constraints

### 4.1 Completeness
- 100% of required columns must have values
- `rul` must be present for training data
- No NULL sensor values allowed
- All 21 sensors required

### 4.2 Validity
- `rul` >= 0 for training data
- Sensor values within documented ranges
- All numeric columns must be valid numbers (no NaN, Inf)
- Engineered features must be computable

### 4.3 Uniqueness
- `feature_id` is unique (no duplicates)
- Each `(engine_id, cycle)` appears exactly once

### 4.4 Consistency
- Sensor values consistent with degradation physics
- `rul` decreases as cycle increases per engine
- No negative RUL jumps within engine lifecycle

### 4.5 Distribution Check
- Training set: 16,000-18,000 rows
- Test set: 2,000-3,000 rows
- No extreme imbalance in engine representation

---

## 5. Data Shape & Statistics

### 5.1 Expected Dimensions
- **Rows (Training)**: ~16,500 records (20,631 total)
- **Columns (Core)**: 28 (3 settings + 21 sensors + target + 3 ID/metadata)
- **Columns (With Engineered)**: ~50
- **Grain**: One row per (engine_id, cycle)

### 5.2 Expected Statistics
- **Missing Values**: 0%
- **Numeric Features**: Mean and StdDev within realistic ranges
- **Outliers**: < 0.5% (flagged in staging, excluded or handled)
- **RUL Distribution**: Skewed right (more early-cycle records)

---

## 6. Acceptance Criteria for ML Ready

✅ **Can proceed to model training if:**
1. All rows have valid, non-null sensor values
2. No duplicate (engine_id, cycle) pairs
3. RUL values are valid (>= 0)
4. Dataset has 15,000+ training rows and 2,000+ test rows
5. No critical data quality issues logged

❌ **Must block training if:**
1. > 5% of rows contain NULL or invalid values
2. RUL has negative or unrealistic values
3. Sensor range violations > 10%
4. Rows are missing from expected engine IDs

---

## 7. Feature Lineage

```
raw_sensor_readings (Contract DC-001)
        ↓
stg_sensor_readings (Contract DC-002)
        ↓
[dbt models: int_engine_lifecycle_windows]
        ↓
fct_equipment_health_features (Contract DC-003)
        ↓
[dbt test: validate_feature_table]
        ↓
model_training_dataset (Mouhcine's training pipeline)
```

---

## 8. Handoff to ML Engineering

Mouhcine receives:

```json
{
  "feature_table": "fct_equipment_health_features",
  "training_rows": 16500,
  "features": 28,
  "target": "rul",
  "train_test_split": "80/20",
  "null_percentage": 0.0,
  "quality_status": "PASS"
}
```

---

## 9. Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 0.1 | 2024-Q3 Sprint 1 | Hamza Elhaddaji | Initial draft |
| 0.2 | 2024-Q3 Sprint 2 | Hamza + Mouhcine | Add engineered features |

---

## 10. Related Artifacts

- 📋 [Staging Contract](./stg_sensor_readings.md)
- 📋 [Raw Contract](./raw_sensor_readings.md)
- 🧪 [dbt Feature Tests](../dbt/models/marts/schema.yml)
- 📊 [Architecture](../docs/architecture.md)
- 🤖 [ML Feature Schema](../src/industrial_health/modeling/feature_schema.json)
