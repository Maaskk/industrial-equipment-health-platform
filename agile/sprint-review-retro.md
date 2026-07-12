# Sprint Review And Retrospective

## Sprint 1

Review:
- Project 7 was selected because predictive maintenance naturally fits MLOps/DataOps.
- Team branches and role files were created.
- NASA C-MAPSS was confirmed as the primary dataset.

Retro:
- What worked: clear ownership helped everyone start independently.
- What did not work: `main` stayed too empty for too long.
- Improvement: integration branch must be updated at least once per sprint.

## Sprint 2

Review:
- DataOps, contracts, EDA, and ML work appeared in separate branches.
- Early API and monitoring utilities were created.
- ML reports showed useful baseline/improved-model comparisons.

Retro:
- What worked: members could work independently.
- What did not work: MLflow, API, and Docker were not connected to the trained model.
- Improvement: every branch needs a tested integration contract before final week.

## Sprint 3

Review:
- Branch work was merged into `integration/final`.
- Full NASA FD001-FD004 training was executed and saved as report/notebook proof.
- API now refuses missing models by default and validates feature schema.
- Docker Compose includes MLflow, training-init, FastAPI, Dagster webserver, and Dagster daemon.

Retro:
- What worked: final integration made the project demonstrable from one branch.
- What did not work: missing Hajar/Akram deliverables had to be rebuilt during integration.
- Improvement: future projects should create issues/milestones early and require PR reviews before merging.

## Final Demo Plan

1. Show README architecture and one-command local run.
2. Show dlt/dbt/DuckDB evidence.
3. Show MLflow experiment and final evaluation report.
4. Call `GET /health`.
5. Call `POST /predict` with `demo/predict_sample.json`.
6. Show prediction log and drift report.
7. Explain limitations honestly.
