# Integration Status

This file records the current production integration state.

## Merged Work

| Area | Branch | Evidence | Status |
|---|---|---|---|
| DataOps | `feature/mohamed-kar1` | dlt ingestion, DuckDB/dbt project, Dagster assets, `tests/test_dataops.py` | merged |
| Data contracts | `feature/HamzaElhaddaji` | contracts, data-quality docs, lineage docs, QA checklist | merged |
| ML modeling | `feature/Mouhcine005` | baseline/improved model scripts, schema, metrics, evaluation report | merged |
| MLOps/API | `owner/Maaskk` | FastAPI service, Docker files, MLflow docs, monitoring, tests, CI workflow | merged |
| Analytics | `feature/ilyass-analytics-eda` | EDA notebook | merged |
| API and demo | `feature/HajarEnnajdy` plus final integration | API contract, example payload, dashboard flow, contract tests | integrated |
| Final QA | `docs/aya-active-team` | monitoring review, Komodo verification, demo checklist, presentation review | active |

## Final consolidation

The production release consolidated compatible work from the feature branches and
added the integration needed to run the whole platform. Current responsibilities
and demonstration ownership are documented in `team/` and
`docs/soutenance/CONTRIBUTIONS_FINAL.md`.

Akram supported the earlier Jira and Agile phase. He is not part of the active
presentation team, and his historical support remains documented.

## Current operating facts

- `main` contains the integrated production project.
- Docker Compose starts MLflow, the training job, FastAPI, Dagster webserver, and Dagster daemon.
- Dagster schedules the full job every day at 06:00 in `Africa/Casablanca`.
- Training registers a candidate and promotes it only when both MAE and RMSE meet the champion rule.
- The Komodo production configuration uses `TRAIN_SUBSETS=FD001`.
- The offline evaluation artifact covers FD001 to FD004 and 707 test engines. These are separate scopes.
