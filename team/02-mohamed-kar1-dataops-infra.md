# Mohamed - DataOps and Infrastructure Automation

GitHub: `mohamed-kar1`

Branch: `feature/mohamed-kar1-dataops-infra`

## Why this role fits

Public GitHub history shows Python pipeline work, DevOps/HCL work, and Jenkins/automation practice. This fits the DataOps foundation and infrastructure automation layer.

## Mission

Build the data pipeline foundation that feeds the ML system.

## Main Deliverables

- dlt ingestion pipeline for predictive-maintenance source data.
- DuckDB warehouse setup.
- Raw and staging table structure.
- Dagster jobs/assets for:
  - ingestion
  - transformation
  - training trigger
  - quality validation
- Local setup scripts.
- Docker Compose support with Ossama.

## Acceptance Criteria

- Raw data can be ingested reproducibly.
- DuckDB contains raw and staging tables.
- Dagster can run the pipeline locally.
- Pipeline outputs a documented feature table path for Mouhcine.
- Commands are documented and tested by another teammate.

## First Tasks

1. Confirm dataset download path and raw schema.
2. Build first dlt source/resource.
3. Write data into DuckDB.
4. Add a Dagster asset for ingestion.
5. Document run commands.
