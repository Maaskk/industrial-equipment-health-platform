# Data Contract: Staging Sensor Readings

## 1. Overview

| Property | Value |
|----------|-------|
| **Contract ID** | `DC-002-STAGING` |
| **Owner** | Hamza Elhaddaji & Mohamed |
| **Status** | Approved and enforced |
| **Last Updated** | 2024-Q3 |
| **Upstream** | `raw_sensor_readings` |
| **Storage** | DuckDB (staging schema) |

---

## 2. Purpose

This contract defines the structure of the **staging layer** after data cleaning and validation. The staging layer is the first transformation step where:
- Data quality issues from raw layer are resolved or flagged
- Consistent formatting is applied
- Invalid records are quarantined
- Data is ready for feature engineering

---

## 3. Table: `stg_sensor_readings`

### 3.1 Schema Definition

| Column Name | Data Type | Nullable | Constraints | Description |
|------------|-----------|----------|-------------|-------------|
| `stg_id` | VARCHAR(50) | NO | UNIQUE, PRIMARY KEY | Surrogate key: `engine_{id}_cycle_{cycle}` |
| `engine_id` | INTEGER | NO | NOT NULL | Engine identifier (from raw) |
| `cycle` | INTEGER | NO | NOT NULL | Operating cycle (from raw) |
| `setting_1` | NUMERIC(10,6) | NO | NOT NULL | Normalized setting 1 |
| `setting_2` | NUMERIC(10,6) | NO | NOT NULL | Normalized setting 2 |
| `setting_3` | NUMERIC(10,6) | NO | NOT NULL | Normalized setting 3 |
| `sensor_1` to `sensor_21` | NUMERIC(10,2) | NO | NOT NULL | 21 sensor readings (imputed if missing) |
| `rul` | NUMERIC(10,2) | YES | >= 0 | Remaining useful life (training only, NULL for predictions) |
| `is_valid` | BOOLEAN | NO | DEFAULT TRUE | Flag: record passed all quality checks |
| `quality_issues` | VARCHAR(500) | YES | - | JSON array of detected issues (if any) |
| `raw_source_file` | VARCHAR(255) | YES | - | Original source file name |
| `outlier_flag` | BOOLEAN | NO | DEFAULT FALSE | Flag if record contains statistical outliers |
| `dbt_created_at` | TIMESTAMP | NO | DEFAULT CURRENT_TIMESTAMP | When staging record was created |
| `dbt_updated_at` | TIMESTAMP | NO | DEFAULT CURRENT_TIMESTAMP | When staging record was last updated |

### 3.2 Expected Characteristics

- **Row Count**: ~20,631 records (from training sets)
- **Grain**: One row per (engine_id, cycle)
- **Duplicates**: Zero (deduplication in dbt model)
- **Completeness**: 100% for sensor readings (imputation applied where needed)

---

## 4. Quality Rules

### 4.1 Data Cleaning Rules (Applied in dbt)
- Remove duplicate `(engine_id, cycle)` pairs (keep first occurrence)
- Impute missing sensor values using forward-fill strategy
- Normalize all sensor values to standard scale
- Flag outliers (> 3 standard deviations from mean)

### 4.2 Validation Rules
- `is_valid = TRUE` only if:
  - No NULL sensor values after imputation
  - All values within valid ranges
  - No orphaned records (missing engine context)

### 4.3 Consistency Rules
- Settings must be consistent with cycle progression
- Sensor degradation expected in later cycles
- No sensor resets within single engine lifecycle

### 4.4 Traceability Rules
- Every row must trace back to raw source (`raw_source_file`)
- `dbt_created_at` and `dbt_updated_at` provide audit trail

---

## 5. Acceptance Criteria

✅ **dbt test must pass if:**
1. No duplicate keys (`stg_id` is unique)
2. No NULL sensor values (after imputation)
3. All sensor values numeric and within valid ranges
4. `is_valid = TRUE` for 99%+ of records
5. Quality issues properly documented for flagged records

❌ **dbt test must fail if:**
1. > 1% of records have `is_valid = FALSE`
2. Duplicate `stg_id` values detected
3. Any NULL sensor values remain
4. Imputation success rate < 95%

---

## 6. Transformations from Raw to Staging

| Transformation | dbt Model | Purpose |
|----------------|-----------|---------|
| Deduplication | `stg_01_deduplicate` | Remove exact duplicate rows |
| Null Imputation | `stg_02_impute_nulls` | Fill missing sensor values |
| Outlier Detection | `stg_03_detect_outliers` | Flag statistical anomalies |
| Validation | `stg_04_validate` | Mark valid/invalid records |
| Final Assembly | `stg_sensor_readings` | Join all validations |

---

## 7. Downstream Contracts

| Downstream Table | Dependency | Validation |
|------------------|-----------|------------|
| `int_engine_lifecycle_windows` | Requires `stg_sensor_readings` clean & complete | Must not contain any invalid records |
| `fct_equipment_health_features` | Depends on staging | Only processes `is_valid = TRUE` |
| `model_training_dataset` | Final input to ML | 100% valid, no nulls |

---

## 8. Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 0.1 | 2024-Q3 Sprint 1 | Hamza Elhaddaji | Initial draft |

---

## 9. Related Artifacts

- 📋 [Raw Sensor Readings Contract](./raw_sensor_readings.md)
- 🧪 [dbt Tests](../dbt/models/staging/schema.yml)
- 📊 [Architecture](../docs/architecture.md)
