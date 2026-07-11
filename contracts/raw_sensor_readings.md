# Data Contract: Raw Sensor Readings

## 1. Overview

| Property | Value |
|----------|-------|
| **Contract ID** | `DC-001-RAW` |
| **Owner** | Hamza Elhaddaji |
| **Status** | Approved and enforced |
| **Last Updated** | 2024-Q3 |
| **Data Source** | NASA C-MAPSS Turbofan Engine Degradation Dataset |
| **Storage** | DuckDB (raw schema) |

---

## 2. Purpose

This contract defines the structure, format, and quality expectations for raw turbofan sensor data ingested from the NASA C-MAPSS dataset. All data entering the warehouse must conform to this contract before proceeding to transformation.

---

## 3. Table: `raw_sensor_readings`

### 3.1 Schema Definition

| Column Name | Data Type | Nullable | Constraints | Range/Format | Description |
|------------|-----------|----------|-------------|-------------|-------------|
| `engine_id` | INTEGER | NO | PRIMARY KEY (part of composite) | 1-100 | Unique identifier for each turbofan engine |
| `cycle` | INTEGER | NO | PRIMARY KEY (part of composite) | 1-368 | Operating cycle number (sequential) |
| `setting_1` | FLOAT | NO | NOT NULL | 0.0-100.0 | Engine operational setting 1 (normalized) |
| `setting_2` | FLOAT | NO | NOT NULL | -0.0072 - 0.84 | Engine operational setting 2 (normalized) |
| `setting_3` | FLOAT | NO | NOT NULL | 9.3496-9.4465 | Engine operational setting 3 (normalized) |
| `sensor_1` | FLOAT | NO | NOT NULL | 518.67-598.76 | Temperature sensor reading (°F) |
| `sensor_2` | FLOAT | NO | NOT NULL | 642.15-645.50 | Temperature sensor reading (°F) |
| `sensor_3` | FLOAT | NO | NOT NULL | 1589.70-2388.06 | Pressure sensor reading |
| `sensor_4` | FLOAT | NO | NOT NULL | 100.00-100.00 | Pressure ratio |
| `sensor_5` | FLOAT | NO | NOT NULL | 84.8-104.4 | Physical sensor reading |
| `sensor_6` | FLOAT | NO | NOT NULL | 7.3-8.4 | Physical sensor reading |
| `sensor_7` | FLOAT | NO | NOT NULL | 0.03-0.04 | Flow rate reading |
| `sensor_8` | FLOAT | NO | NOT NULL | 392-522 | Rotational speed |
| `sensor_9` | FLOAT | NO | NOT NULL | 2388.01-2388.04 | Power reading |
| `sensor_10` | FLOAT | NO | NOT NULL | 100.00-100.10 | Percentage reading |
| `sensor_11` | FLOAT | NO | NOT NULL | 47.4-521.0 | Vibration reading |
| `sensor_12` | FLOAT | NO | NOT NULL | 2388.01-2388.05 | Power reading |
| `sensor_13` | FLOAT | NO | NOT NULL | 8.3584-8.4290 | Ratio reading |
| `sensor_14` | FLOAT | NO | NOT NULL | 0.03-0.04 | Rate reading |
| `sensor_15` | FLOAT | NO | NOT NULL | 392.0-522.0 | Speed reading |
| `sensor_16` | FLOAT | NO | NOT NULL | 537.71-2388.04 | Temperature reading |
| `sensor_17` | FLOAT | NO | NOT NULL | 100.0-100.1 | Percentage reading |
| `sensor_18` | FLOAT | NO | NOT NULL | 8.9-9.0 | Pressure ratio |
| `sensor_19` | FLOAT | NO | NOT NULL | 0.03-0.04 | Flow reading |
| `sensor_20` | FLOAT | NO | NOT NULL | 100.0-100.0 | Percentage reading |
| `sensor_21` | FLOAT | NO | NOT NULL | 39.06-735.84 | Turbulence reading |
| `rul` | INTEGER | NO | NOT NULL | 0-360 | **Remaining Useful Life (RUL)** - target variable, training only |
| `data_source` | VARCHAR(100) | YES | DEFAULT 'nasa-cmapss' | - | Origin of the data file |
| `file_name` | VARCHAR(255) | YES | - | - | Source file name for traceability |
| `loaded_at` | TIMESTAMP | NO | DEFAULT CURRENT_TIMESTAMP | - | UTC timestamp when record was loaded into warehouse |
| `load_batch_id` | VARCHAR(50) | YES | - | - | Batch identifier for audit trail |

---

## 4. Quality Rules

### 4.1 Completeness
- All `NOT NULL` columns must have values
- No empty strings in string columns
- Missing sensor readings = Pipeline failure

### 4.2 Validity
- `engine_id` must be > 0
- `cycle` must be >= 1 and sequential per engine (no gaps)
- All sensor values must be numeric (no NaN or Inf)
- Settings and sensors must be within documented ranges
- `rul` >= 0 (no negative remaining life)

### 4.3 Uniqueness
- Composite key `(engine_id, cycle)` must be unique
- No duplicate records in a single load batch

### 4.4 Consistency
- All 21 sensors present for every record
- Settings consistent with engine operational state
- Sensor values consistent with physics constraints (e.g., temperature monotonicity in degradation)

### 4.5 Freshness
- `loaded_at` timestamp <= current time
- Max age of raw data: unlimited (historical training data is valid)

### 4.6 Referential Integrity
- `engine_id` must match expected range (1-100 for training sets)
- All numeric values must be within sensor specification ranges

---

## 5. Acceptance Criteria

✅ **Pipeline passes if:**
1. 100% of rows conform to schema (data types, nullability)
2. No duplicate `(engine_id, cycle)` pairs
3. All mandatory quality rules pass
4. Row count matches expected dataset size ± 0.1%
5. No data loaded with timestamps in the future

❌ **Pipeline fails if:**
1. Missing required columns
2. Data type mismatches
3. Null values in NOT NULL columns
4. Sensor values outside documented ranges by >5%
5. Duplicate keys detected

---

## 6. Lineage & Ownership

| Role | Responsibility |
|------|-----------------|
| **Mohamed (Ingestion)** | Load raw files into DuckDB using dlt |
| **Hamza (Quality)** | Define contract, enforce via dbt tests |
| **Ossama (Orchestration)** | Fail pipeline on contract breach |

---

## 7. Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 0.1 | 2024-Q3 Sprint 1 | Hamza Elhaddaji | Initial draft from NASA C-MAPSS specs |

---

## 8. Related Artifacts

- 📊 [Architecture](../docs/architecture.md)
- 🧪 [dbt Tests](../dbt/models/raw/schema.yml)
- 📈 [Data Quality Monitoring](../docs/data-quality.md)
- 🔄 [Lineage Diagram](../docs/data-lineage.md)
