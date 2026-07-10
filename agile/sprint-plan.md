# Sprint Plan

## Sprint 1: Foundations

Goal: make the project skeleton collaborative and ingest real data.

| Work | Owner | Evidence |
|---|---|---|
| Repository, branches, team task files | Ossama | `team/`, branch plan docs |
| NASA C-MAPSS source and license documentation | Hamza | `docs/data-sources-and-licenses.md` |
| dlt raw ingestion into DuckDB | Mohamed | `src/industrial_health/ingestion/dlt_pipeline.py` |
| Initial EDA notebook | Ilyass | `mlops_project/notebooks/EDA.ipynb` |

Review outcome: dataset and architecture were selected, but main integration was still weak.

## Sprint 2: DataOps And Modeling

Goal: transform raw data and build a defensible ML baseline.

| Work | Owner | Evidence |
|---|---|---|
| dbt staging and marts | Mohamed | `dbt_project/models/` |
| data contract, lineage, QA checklist | Hamza | `contracts/`, `docs/data-lineage.md`, `docs/qa_checklist.md` |
| baseline and improved ML reports | Mouhcine | `ml-modeling/` |
| API and MLOps skeleton | Ossama/Hajar | `src/industrial_health/api/`, `src/industrial_health/mlops/` |

Review outcome: good component work existed, but branches were not merged and MLflow/API were not fully connected.

## Sprint 3: Final Integration

Goal: turn scattered components into one reproducible local MLOps/DataOps platform.

| Work | Owner | Evidence |
|---|---|---|
| merge teammate branches into `integration/final` | Ossama | `docs/integration-status.md` |
| full FD001-FD004 training proof | Ossama/Mouhcine | `scripts/train_model.py`, `reports/model_metrics/final_evaluation.json`, `notebooks/training_executed.ipynb` |
| strict API schema and no silent fallback | Ossama/Hajar | `docs/api.md`, `tests/test_maaskk_api_app.py` |
| Docker Compose one-command stack | Ossama/Mohamed | `docker-compose.yml`, `Dockerfile` |
| CI gates and release docs | Ossama/Akram | `.github/workflows/ci.yml`, `docs/release-checklist.md` |

Review outcome: final branch is the release candidate. `main` should be updated only after verification and review.
