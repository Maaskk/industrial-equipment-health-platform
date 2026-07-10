# Data Lineage Diagram

**Document Owner**: Hamza Elhaddaji  
**Last Updated**: Q3 2024  
**Status**: Draft

---

## 1. Overall Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LINEAGE ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   EXTERNAL DATA  │
│  NASA C-MAPSS    │
│  Turbofan Data   │
│  (CSV Files)     │
└────────┬─────────┘
         │
         │ dlt (Mohamed)
         │ Extract & Load
         ▼
┌──────────────────────────────────┐
│   RAW LAYER (raw schema)         │
│   ✓ raw_sensor_readings          │
│   ✓ 21 Sensors + Settings        │
│   ✓ ~20,631 records              │
│   [Contract: DC-001-RAW]         │
│   [Owner: Mohamed + Hamza]       │
└────────┬─────────────────────────┘
         │
         │ dbt Transformations (Mohamed/Hamza)
         │ ├─ Deduplication
         │ ├─ Quality Validation
         │ └─ Null Imputation
         │
         ▼
┌──────────────────────────────────┐
│  STAGING LAYER (stg schema)      │
│  ✓ stg_sensor_readings           │
│  ✓ Clean & Validated Data        │
│  ✓ ~20,631 records (deduplicated)│
│  ✓ Quality flags & issues        │
│  [Contract: DC-002-STAGING]      │
│  [Owner: Hamza]                  │
└────────┬─────────────────────────┘
         │
         │ dbt Models (Hamza)
         │ ├─ Feature Engineering
         │ ├─ Aggregations
         │ └─ Window Functions
         │
         ▼
┌──────────────────────────────────┐
│ INTERMEDIATE LAYER (int schema)  │
│ ├─ int_engine_lifecycle_windows  │
│ ├─ int_sensor_degradation_rates  │
│ ├─ int_engine_statistics         │
│ [Owner: Hamza]                   │
└────────┬─────────────────────────┘
         │
         │ dbt Models (Hamza/Mouhcine)
         │ ├─ Feature Assembly
         │ ├─ Target Engineering
         │ └─ Train/Test Split
         │
         ▼
┌──────────────────────────────────┐
│  FEATURE LAYER (marts schema)    │
│  ✓ fct_equipment_health_features │
│  ✓ ML-Ready Data                 │
│  ✓ ~16,500 train + 2,000 test    │
│  [Contract: DC-003-FEATURES]     │
│  [Owner: Hamza + Mouhcine]       │
└────────┬─────────────────────────┘
         │
         │ Python Pipeline (Mouhcine)
         │ ├─ Feature Scaling
         │ ├─ Data Validation
         │ └─ Train/Test Split
         │
         ▼
┌──────────────────────────────────┐
│     ML TRAINING DATASET          │
│  ✓ training_data.parquet         │
│  ✓ test_data.parquet             │
│  [Owner: Mouhcine]               │
└────────┬─────────────────────────┘
         │
         │ sklearn/XGBoost
         │ ├─ Model Training
         │ ├─ Hyperparameter Tuning
         │ └─ Cross-validation
         │
         ▼
┌──────────────────────────────────┐
│    TRAINED ML MODELS             │
│  ✓ model_v1.pkl (Random Forest)  │
│  ✓ model_v2.pkl (XGBoost)        │
│  ✓ model_metadata.json           │
│  [Owner: Mouhcine]               │
└──────────────────────────────────┘
```

---

## 2. Detailed Layer-by-Layer Lineage

### 2.1 Raw Layer Lineage

```
NASA C-MAPSS Dataset (CSV)
│
├─ train_FD001.txt
├─ train_FD002.txt
├─ train_FD003.txt
└─ train_FD004.txt
│
└─ dlt Pipeline (Mohamed)
   └─ SQL: INSERT INTO raw.raw_sensor_readings
      └─ raw_sensor_readings (21 sensors + settings + RUL)
         │
         ├─ 21 x sensor columns (FLOAT)
         ├─ 3 x setting columns (FLOAT)
         ├─ 1 x RUL column (INTEGER)
         ├─ 1 x engine_id (INTEGER)
         ├─ 1 x cycle (INTEGER)
         └─ Metadata (source_file, loaded_at)
         
[Quality Gates]
✓ NOT NULL on all required columns
✓ Value ranges validated
✓ Uniqueness on (engine_id, cycle)
✓ Row count: 20,631 ± 5%
```

### 2.2 Staging Layer Lineage

```
raw.raw_sensor_readings
│
└─ dbt Model: stg_01_deduplicate
   │
   └─ Transformation: Remove exact duplicates
      └─ stg_deduplicated
         │
         └─ dbt Model: stg_02_impute_nulls
            │
            └─ Transformation: Forward-fill missing sensors
               └─ stg_imputed
                  │
                  └─ dbt Model: stg_03_detect_outliers
                     │
                     └─ Transformation: Flag statistical anomalies
                        └─ stg_with_outliers
                           │
                           └─ dbt Model: stg_04_validate
                              │
                              └─ Transformation: Run quality checks
                                 └─ stg_validated
                                    │
                                    └─ dbt Model: stg_sensor_readings
                                       │
                                       └─ Final Staging Table
                                          ├─ stg_id (PK)
                                          ├─ 21 x sensor (all populated)
                                          ├─ is_valid (flag)
                                          ├─ quality_issues (JSON)
                                          ├─ outlier_flag
                                          └─ dbt_created_at

[Quality Gates]
✓ 0 duplicate keys (stg_id unique)
✓ 100% of sensors populated (post-imputation)
✓ is_valid = TRUE for 99%+ records
✓ quality_issues documented for flagged records
✓ Row count: 20,631 ± 2%
```

### 2.3 Intermediate Layer Lineage

```
stg.stg_sensor_readings
│
├─ dbt Model: int_engine_lifecycle_windows
│  │
│  ├─ Transformation: Create rolling windows per engine
│  │  - 5-cycle rolling statistics
│  │  - Degradation rates
│  │  - Cycle position normalization
│  │
│  └─ Output: int_engine_lifecycle_windows
│     ├─ engine_id
│     ├─ cycle
│     ├─ All 21 sensors
│     ├─ rolling_mean_5 (each sensor)
│     ├─ rolling_std_5 (each sensor)
│     └─ cycle_norm
│
├─ dbt Model: int_sensor_degradation_rates
│  │
│  ├─ Transformation: Calculate rate of change
│  │  - Change per cycle
│  │  - Acceleration (second derivative)
│  │
│  └─ Output: int_sensor_degradation_rates
│     ├─ engine_id
│     ├─ cycle
│     ├─ sensor_1_rate
│     ├─ sensor_1_acceleration
│     └─ ... (for all 21 sensors)
│
└─ dbt Model: int_engine_statistics
   │
   ├─ Transformation: Summary statistics per engine
   │  - Mean, Std, Min, Max per sensor
   │  - Health score
   │
   └─ Output: int_engine_statistics
      ├─ engine_id
      ├─ sensor_1_mean
      ├─ sensor_1_std
      └─ ... (statistics for all sensors)
```

### 2.4 Features Layer Lineage

```
int_engine_lifecycle_windows
int_sensor_degradation_rates
int_engine_statistics
│
└─ dbt Model: fct_equipment_health_features
   │
   ├─ JOIN: Combine all intermediate models
   ├─ SELECT: Core features (21 sensors + settings + RUL)
   ├─ SELECT: Engineered features (rolling stats, degradation rates)
   ├─ COMPUTE: Train/Test Split (80/20)
   ├─ FILTER: Only valid records (is_valid = TRUE)
   │
   └─ Output: fct_equipment_health_features
      ├─ feature_id (PK)
      ├─ engine_id
      ├─ cycle
      ├─ 3 x setting columns
      ├─ 21 x sensor columns
      ├─ RUL (target)
      ├─ dataset_split (train/test)
      └─ metadata (created_at, model_version)

[Quality Gates]
✓ 0 NULL values in any feature
✓ All numeric values valid (no NaN/Inf)
✓ Unique (engine_id, cycle)
✓ 80/20 train/test split
✓ No data leakage between splits
✓ Row count: Train 16,500 | Test 2,000
```

---

## 3. Data Ownership Matrix

| Layer | Table | Owner(s) | Maintainer | Status |
|-------|-------|----------|-----------|--------|
| Raw | raw_sensor_readings | Mohamed | Mohamed | 🟢 Active |
| Staging | stg_sensor_readings | Hamza | Hamza | 🟡 Draft |
| Intermediate | int_* | Hamza | Hamza | 🟡 Draft |
| Features | fct_equipment_health_features | Hamza, Mouhcine | Hamza/Mouhcine | 🟡 Draft |
| ML | training_dataset | Mouhcine | Mouhcine | 🟡 Draft |

---

## 4. Transformation Flows

### 4.1 Raw → Staging Transformations

| Step | dbt Model | Logic | Source | Target |
|------|-----------|-------|--------|--------|
| 1 | stg_01_deduplicate | Remove exact duplicates | raw_sensor_readings | stg_deduplicated |
| 2 | stg_02_impute_nulls | Forward-fill missing sensors | stg_deduplicated | stg_imputed |
| 3 | stg_03_detect_outliers | Flag 3-sigma outliers | stg_imputed | stg_with_outliers |
| 4 | stg_04_validate | Run quality checks | stg_with_outliers | stg_validated |
| 5 | stg_sensor_readings | Final assembly | stg_validated | stg_sensor_readings |

### 4.2 Staging → Features Transformations

| Step | dbt Model | Logic | Source | Target |
|------|-----------|-------|--------|--------|
| 1 | int_engine_lifecycle_windows | Create rolling windows | stg_sensor_readings | int_engine_lifecycle_windows |
| 2 | int_sensor_degradation_rates | Calculate change rates | stg_sensor_readings | int_sensor_degradation_rates |
| 3 | int_engine_statistics | Summary statistics | stg_sensor_readings | int_engine_statistics |
| 4 | fct_equipment_health_features | Join intermediates | all int_* | fct_equipment_health_features |

---

## 5. Data Dependencies Graph

```
Upstream Dependencies:
└─ raw_sensor_readings
   ├─ stg_sensor_readings
   │  ├─ int_engine_lifecycle_windows
   │  │  └─ fct_equipment_health_features
   │  │     └─ training_dataset
   │  │
   │  ├─ int_sensor_degradation_rates
   │  │  └─ fct_equipment_health_features
   │  │     └─ training_dataset
   │  │
   │  └─ int_engine_statistics
   │     └─ fct_equipment_health_features
   │        └─ training_dataset
```

**Materialization Strategy**:
- Raw: Table (immutable)
- Staging: Table (rebuilt daily)
- Intermediate: View (computed on demand)
- Features: Table (rebuilt on schedule)

---

## 6. Testing & Validation Lineage

```
dbt Test Chain:

raw_sensor_readings Tests
├─ not_null: [engine_id, cycle, sensors_1..21, rul]
├─ unique: [engine_id, cycle]
├─ accepted_values: engine_id IN (1..100)
├─ expect_column_values_to_be_between: all sensors
└─ row_count_between: 20000..21000

→ If ALL pass, proceed to staging

stg_sensor_readings Tests
├─ not_null: [sensors_1..21 after imputation]
├─ unique: stg_id
├─ accepted_values: dataset_split IN ('train','test','val')
├─ expect_column_values_to_be_between: all sensors
└─ row_count_between: 19000..21000

→ If ALL pass, proceed to features

fct_equipment_health_features Tests
├─ not_null: [all features, RUL]
├─ unique: [engine_id, cycle]
├─ row_count_between_train: 15000..18000
├─ row_count_between_test: 2000..4000
└─ data_types: all numeric

→ If ALL pass, approve for ML training
```

---

## 7. Change Management

### 7.1 Schema Changes

When updating lineage (e.g., adding new feature):

```
1. Update dbt model
2. Update schema.yml tests
3. Update contract document
4. Run dbt test
5. Document change in lineage
6. Get peer review
7. Merge to main
8. Monitor for data quality issues
```

### 7.2 Breaking Changes

**Never**:
- ❌ Delete columns from production tables
- ❌ Change data types without migration
- ❌ Remove dbt tests

**Always**:
- ✅ Create new columns for changes
- ✅ Deprecate old columns gradually
- ✅ Document all changes
- ✅ Communicate with downstream users

---

## 8. Related Artifacts

- 📋 [Data Contracts](../contracts/)
- 🧪 [dbt Models & Tests](../dbt/)
- 📊 [Data Quality Documentation](./data-quality.md)
- ✅ [QA Checklist](./qa-checklist.md)
- 📈 [Architecture](./architecture.md)

---

**Last Updated**: Q3 2024  
**Next Review**: End of Sprint 2
