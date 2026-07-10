# Product Backlog

Product: Industrial Equipment Health Platform

Group name: AeroReliability Lab

## User Stories

| ID | Priority | Owner | Story | Acceptance criteria |
|---|---:|---|---|---|
| PB-01 | P0 | Mohamed | As a data engineer, I need NASA C-MAPSS files ingested into DuckDB so the team has one trusted local warehouse. | dlt loads FD001-FD004 train/test/RUL files; raw tables exist; row counts are documented. |
| PB-02 | P0 | Hamza | As a quality owner, I need contracts and dbt tests so bad data is caught before training. | dbt run succeeds; dbt test passes; contracts document raw, staging, and mart fields. |
| PB-03 | P0 | Mouhcine | As an ML engineer, I need leakage-safe training and baseline comparisons so model quality is defensible. | Mean, cycle-only, Ridge, RandomForest, and final boosting metrics are saved. |
| PB-04 | P0 | Ossama | As an MLOps lead, I need MLflow tracking and a saved serving artifact so the model is reproducible. | Training logs metrics/artifacts to MLflow and writes `models/latest/model.pkl`. |
| PB-05 | P0 | Hajar | As a demo user, I need a clear API contract so predictions can be tested confidently. | `/health` and `/predict` documented; generated payload works; invalid fields return 422. |
| PB-06 | P0 | Ossama | As a reviewer, I need one command to launch the stack locally. | `docker compose up --build` starts MLflow, training-init, FastAPI, Dagster webserver, and Dagster daemon. |
| PB-07 | P1 | Ilyass | As a stakeholder, I need EDA and business evidence so the project value is clear. | EDA notebook summarizes engines, cycles, sensors, and RUL patterns. |
| PB-08 | P1 | Ossama | As an operator, I need monitoring proof so API use is traceable. | Predictions are logged; drift report command writes `reports/monitoring/drift_report.json`. |
| PB-09 | P1 | Akram | As a project manager, I need sprint and release artifacts so the course Agile requirement is covered. | Sprint plan, review/retro, release checklist, and final report exist. |
| PB-10 | P2 | Team | As a professor, I need honest documentation so I can reproduce the project without hidden manual steps. | README, API guide, data license docs, and final report reference tested commands. |

## Definition Of Done

- Code is committed on `integration/final`.
- Tests or command evidence exist for the changed area.
- Generated raw data and local runtime databases are not committed.
- Docs name exact commands, outputs, and limitations.
- Demo behavior uses the real trained model unless a test explicitly enables fallback.
