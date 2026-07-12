# Integration Status

This file records the integration state for the final project branch.

## Merged Work

| Area | Branch | Evidence | Status |
|---|---|---|---|
| DataOps | `feature/mohamed-kar1` | dlt ingestion, DuckDB/dbt project, Dagster assets, `tests/test_dataops.py` | merged |
| Data contracts | `feature/HamzaElhaddaji` | contracts, data-quality docs, lineage docs, QA checklist | merged |
| ML modeling | `feature/Mouhcine005` | baseline/improved model scripts, schema, metrics, evaluation report | merged |
| MLOps/API | `owner/Maaskk` | FastAPI service, Docker files, MLflow docs, monitoring, tests, CI workflow | merged |
| Analytics | `feature/ilyass-analytics-eda` | EDA notebook | merged |

## Rebuilt By Integration

- Hajar's `feature/HajarEnnajdy` branch had no visible commits beyond the scaffold, so the final integration branch must implement the API/demo documentation and sample payloads.
- Akram's `feature/Adonis-I` branch had no visible commits beyond `main`, so the final integration branch must implement backlog, sprint artifacts, release checklist, and final presentation/report coordination.

## Current Integration Risks

- `main` still does not contain the integrated project until `integration/final` is merged.
- The current model branch is a good baseline, but the final project still needs a reproducible training script, executed notebook proof, and MLflow registration evidence.
- The existing API fallback model must be disabled by default before final demo.
- Docker Compose must become the single-command local runtime required by the professor.
