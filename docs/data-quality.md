# Data Quality Strategy & Monitoring

**Document Owner**: Hamza Elhaddaji  
**Last Updated**: 2026-07-11
**Status**: Final integration baseline

---

## 1. Executive Summary

This document outlines the data quality framework for the Industrial Equipment Health Platform. Quality is enforced through three mechanisms:

1. **Contracts** - Define expected data structure and quality rules
2. **dbt Tests** - Automated validation at each data layer
3. **Monitoring** - Continuous quality checks on production data

---

## 2. Quality Dimensions

### 2.1 Completeness
**Definition**: All required fields contain values; no missing data in critical columns.

| Layer | Target | Test Method | Owner |
|-------|--------|-------------|-------|
| Raw | 100% non-null sensor readings | dbt not_null test | Mohamed |
| Staging | 100% non-null sensors (after imputation) | dbt not_null test | Hamza |
| Features | 100% non-null features for ML | dbt not_null test | Hamza/Mouhcine |

**Acceptable Gaps**: 
- Raw: 0% (loading fails if missing)
- Staging: 0% (imputation fills gaps)
- Features: 0% (ML training requires 100%)

---

### 2.2 Validity
**Definition**: Data values conform to expected format, type, and range.

| Dimension | Raw | Staging | Features |
|-----------|-----|---------|----------|
| **Data Type** | INTEGER, FLOAT | NUMERIC | NUMERIC |
| **Range Checks** | ✅ Sensor ranges | ✅ Same ranges | ✅ Same ranges |
| **Format Checks** | ✅ No NaN/Inf | ✅ No NaN/Inf | ✅ No NaN/Inf |
| **Business Rules** | ✅ engine_id 1-100 | ✅ Inherited | ✅ Inherited |

**dbt Tests Applied**:
```yaml
- dbt_expectations.expect_column_values_to_be_between
- dbt_expectations.expect_column_values_to_be_in_type_list
- accepted_values tests for categorical columns
```

---

### 2.3 Uniqueness
**Definition**: No duplicate records; each record is distinct.

| Layer | Uniqueness Key | Test | Tolerance |
|-------|---|---|---|
| Raw | (engine_id, cycle) | Compound unique | 0 duplicates |
| Staging | stg_id | Primary key | 0 duplicates |
| Features | (engine_id, cycle) | Compound unique | 0 duplicates |

**Impact**: Duplicates break model training and cause data leakage.

---

### 2.4 Consistency
**Definition**: Data is logically coherent; rules and constraints are satisfied.

**Key Consistency Rules**:
1. **Monotonicity**: RUL should decrease (or stay same) as cycle increases per engine
2. **Temporal**: Sensor trends should reflect engine degradation
3. **Cross-field**: Settings should correlate with sensor readings
4. **Referential**: All engine_ids reference valid engines (1-100)

**dbt Test**:
```yaml
tests:
  - dbt_expectations.expect_column_values_to_be_decreasing:
      column_name: rul
      group_by: [engine_id]
```

---

### 2.5 Accuracy
**Definition**: Data correctly represents real-world measurements.

**For NASA C-MAPSS Data**:
- No manual interventions needed (sourced from reliable scientific dataset)
- Sensor values verified against physics constraints
- RUL calculated from historical degradation patterns

**Validation Method**: Outlier detection at staging layer

---

### 2.6 Timeliness
**Definition**: Data is fresh and available when needed.

| Layer | Freshness | Update Frequency | SLA |
|-------|-----------|-----------------|-----|
| Raw | Historical (training) | One-time load | N/A |
| Staging | Same as raw | During ingestion | < 1 hour |
| Features | Same as staging | During orchestration | < 2 hours |

---

## 3. Quality Rules by Layer

### 3.1 Raw Layer Quality Rules

```sql
-- Rule 1: No null sensor values
NOT NULL on: setting_1..3, sensor_1..21, rul

-- Rule 2: Value ranges
CHECK setting_1 BETWEEN 0 AND 100
CHECK setting_2 BETWEEN -1 AND 1
CHECK setting_3 BETWEEN 9 AND 10
CHECK sensor_1 BETWEEN 500 AND 650
-- ... (all sensors)
CHECK rul BETWEEN 0 AND 360

-- Rule 3: Uniqueness
UNIQUE on: (engine_id, cycle)

-- Rule 4: Referential integrity
engine_id IN (1..100)
cycle >= 1

-- Rule 5: Row count validation
COUNT(*) BETWEEN 20,000 AND 21,000
```

### 3.2 Staging Layer Quality Rules

```sql
-- Rule 1: All sensors populated after imputation
NOT NULL on: sensor_1..21

-- Rule 2: Deduplication
UNIQUE on: (engine_id, cycle)

-- Rule 3: Validity flagging
is_valid = TRUE if all quality checks pass
is_valid = FALSE if any issues detected

-- Rule 4: Quality issues documented
quality_issues column contains JSON array of issues

-- Rule 5: Outlier detection
outlier_flag = TRUE if value > 3 std from mean
```

### 3.3 Features Layer Quality Rules

```sql
-- Rule 1: ML Readiness
- No NULL values in any feature
- All features numeric
- No NaN or Inf values
- Target (RUL) present and valid

-- Rule 2: Grain Validation
- Exactly one row per (engine_id, cycle)
- No data leakage between train/test

-- Rule 3: Split Validation
- Training set: 80% of data
- Test set: 20% of data
- Stratified by engine_id
```

---

## 4. dbt Test Implementation

### 4.1 Test File Structure

```
dbt/models/
├── raw/
│   └── schema.yml          # Raw layer tests
├── staging/
│   └── schema.yml          # Staging layer tests
└── marts/
    └── schema.yml          # Features layer tests
```

### 4.2 Running Tests

```bash
# Run all tests
dbt test

# Run tests for specific layer
dbt test -s tag:raw
dbt test -s tag:staging
dbt test -s tag:marts

# Run specific test
dbt test -s raw_sensor_readings.engine_id_not_null
```

### 4.3 Test Results Interpretation

**Pass (✅)**: Data conforms to contract
**Warn (⚠️)**: Data mostly OK, investigate anomalies
**Fail (❌)**: Data violates critical constraint, pipeline blocks

---

## 5. Quality Monitoring & Alerts

### 5.1 Monitoring Strategy

| Metric | Tool | Frequency | Alert Threshold |
|--------|------|-----------|-----------------|
| Row Count | dbt | Per pipeline run | ±5% from expected |
| Null % | dbt | Per pipeline run | > 1% |
| Duplicate % | dbt | Per pipeline run | > 0% |
| Outlier % | dbt | Per pipeline run | > 5% |
| Data Freshness | Dagster | Hourly | > 2 hours stale |

### 5.2 Alerting

Alerts are configured in the Dagster orchestration layer:

```yaml
alerts:
  - type: null_check
    column: sensor_1
    threshold: 5
    action: email_admin

  - type: duplicate_check
    key: [engine_id, cycle]
    threshold: 1
    action: slack_notification

  - type: freshness_check
    table: stg_sensor_readings
    max_age_hours: 2
    action: escalate
```

---

## 6. Quality Scorecard

### 6.1 Current Status

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Completeness** | 100% | Pending | 🟡 |
| **Validity** | 100% | Pending | 🟡 |
| **Uniqueness** | 100% | Pending | 🟡 |
| **Consistency** | 100% | Pending | 🟡 |
| **Test Coverage** | 80%+ | Draft | 🟡 |

### 6.2 Quality SLAs

| Layer | SLA | Consequence |
|-------|-----|-------------|
| Raw | 95%+ pass rate | Alert ops team |
| Staging | 99%+ pass rate | Fail pipeline |
| Features | 100% pass rate | Block ML training |

---

## 7. Data Quality Incidents

### 7.1 Incident Response Process

1. **Detection**: dbt test fails or alert triggered
2. **Investigation**: Check data quality report and logs
3. **Root Cause**: Identify source of issue
4. **Resolution**: Fix data or update rules
5. **Validation**: Rerun tests to confirm fix
6. **Documentation**: Log incident and prevention

### 7.2 Common Issues & Resolutions

| Issue | Cause | Resolution | Owner |
|-------|-------|-----------|-------|
| Null sensors | Missing values in raw | Imputation via forward-fill | Hamza |
| Out-of-range | Sensor calibration drift | Review calibration specs | Mohamed |
| Duplicates | Duplicate file loads | Deduplication check | Ossama |
| Missing engines | Incomplete dataset | Validate source file | Mohamed |

---

## 8. Quality Documentation

### 8.1 Required Artifacts

- ✅ Data contracts (3 files)
- ✅ dbt tests (schema.yml files)
- ✅ Data quality documentation (this file)
- 📝 Data lineage diagram
- 📝 Quality QA checklist

### 8.2 Test Documentation Template

Each dbt test should include:
```yaml
- name: expect_column_values_to_be_between
  description: "Validates sensor_1 readings are within expected range"
  tests:
    - dbt_expectations.expect_column_values_to_be_between:
        min_value: 500
        max_value: 650
        config:
          severity: error  # Block on fail
          where: "loaded_at >= current_date - 1"  # Recent data only
```

---

## 9. Quality Assurance Checklist

See `qa-checklist.md` for detailed QA review criteria.

Key checkpoints:
- [ ] All contracts peer-reviewed
- [ ] All dbt tests passing
- [ ] Quality scorecard reviewed
- [ ] Monitoring configured
- [ ] Incident playbooks documented
- [ ] Team sign-off obtained

---

## 10. Future Enhancements

**Sprint 2+**:
- [ ] Build Dagster quality observability dashboard
- [ ] Implement Great Expectations for advanced validation
- [ ] Create ML data quality monitoring
- [ ] Implement data profiling for trend detection
- [ ] Automated quality reports to stakeholders

---

## 11. Contact & Escalation

| Role | Contact | Escalation |
|------|---------|-----------|
| **Data Quality Lead** | Hamza Elhaddaji | Quality issues |
| **Data Engineering Lead** | Mohamed | Data ingestion issues |
| **Orchestration Lead** | Ossama | Pipeline failures |
| **ML Lead** | Mouhcine | Feature issues |

---

**Document History**:
- v0.1 (Q3 2024): Initial draft by Hamza
- v1.0 (2026-07-11): Final integration, dbt/DuckDB training gate, and leakage-safe mart
- v0.2: Pending team review
