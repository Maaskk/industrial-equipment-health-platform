# Data Contracts Directory

This directory contains the data quality contracts that define the expected structure, format, and quality standards for all data layers in the Industrial Equipment Health Platform.

## 📋 Contracts Overview

### 1. `raw_sensor_readings.md`
- **Purpose**: Define raw data ingestion contract from NASA C-MAPSS dataset
- **Owner**: Mohamed (Ingestion) + Hamza (Quality)
- **Status**: Approved and enforced
- **Key Sections**: Schema, quality rules, acceptance criteria, lineage
- **Enforced By**: ingestion checks and `../dbt_project/models/schema.yml`

### 2. `stg_sensor_readings.md`
- **Purpose**: Define staging/cleaning layer after data transformation
- **Owner**: Hamza (Quality)
- **Status**: Approved and enforced
- **Key Sections**: Data cleaning rules, transformations, validation logic
- **Enforced By**: `../dbt_project/models/schema.yml`

### 3. `fct_equipment_health_features.md`
- **Purpose**: Define final ML-ready feature table
- **Owner**: Hamza (Quality) + Mouhcine (ML)
- **Status**: Approved and enforced
- **Key Sections**: Feature schema, ML readiness criteria, handoff specs
- **Enforced By**: `../dbt_project/models/schema.yml`

---

## 🔄 Contract Enforcement

Each contract is enforced through:
1. **dbt tests** in `schema.yml` files (automated validation)
2. **dbt models** in respective layer folders
3. **Python tests** in `../tests/test_dataops.py`

### Quality Gate Flow
```
Raw Data (Mohamed)
    ↓ [Contract: raw_sensor_readings]
    ↓ [dbt tests: uniqueness, nullness, ranges]
    ↓
Staging (Hamza)
    ↓ [Contract: stg_sensor_readings]
    ↓ [dbt tests: deduplication, imputation, outliers]
    ↓
Features (Hamza + Mouhcine)
    ↓ [Contract: fct_equipment_health_features]
    ↓ [dbt tests: completeness, ML readiness]
    ↓
ML Training (Mouhcine)
```

---

## 📊 Related Documentation

- `../docs/data-quality.md` - Data quality monitoring and dashboards
- `../docs/data-lineage.md` - Complete data lineage diagram
- `../docs/qa-checklist.md` - Documentation QA checklist
- `../dbt_project/models/schema.yml` - dbt test definitions

---

## 🛠️ How to Use These Contracts

### For Data Engineers
1. Read the contract for your layer
2. Implement transformations according to spec
3. Create dbt tests to enforce quality rules
4. Commit to your feature branch

### For QA/Documentation
1. Review contracts for completeness
2. Validate against actual data
3. Document any deviations
4. Update QA checklist

### For ML Engineers
1. Review `fct_equipment_health_features.md` contract
2. Validate training data against spec
3. Report any issues back to data team
4. Document feature versions

---

## ✅ Acceptance Criteria

Contracts are complete when:
- [x] All 3 contracts reviewed for final integration
- [x] dbt tests implemented and passing locally
- [x] Data quality documentation complete
- [x] Data lineage documented
- [x] Final training consumes the dbt/DuckDB output

---

## 📝 Version Control

All contracts are versioned in git. Track changes via:
```bash
git log --oneline -- contracts/
git diff contracts/raw_sensor_readings.md
```

---

**Last Updated**: 2026-07-11
**Owner**: Hamza Elhaddaji (Quality & Documentation Lead)
