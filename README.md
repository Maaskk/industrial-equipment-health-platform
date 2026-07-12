# Industrial Equipment Health Platform

Predictive maintenance MLOps project for industrial turbofan sensor data.

This repository is designed for the MLOps & DataOps final project. The goal is not only to train a model, but to industrialize the full lifecycle of a data product: ingestion, storage, transformation, quality, orchestration, model training, tracking, serving, CI/CD, monitoring, and documentation.

## Project Choice

Selected subject from the official list:

**Project 7 - Maintenance predictive industrielle**

Product framing:

**Industrial Equipment Health Platform: Predictive Maintenance with MLOps and DataOps**

The platform predicts equipment degradation risk and remaining useful life from multivariate sensor readings. The final dataset is NASA C-MAPSS turbofan degradation data.

## Final Local Run

The professor allowed local Docker/Docker Compose delivery. From a fresh clone, the intended command is:

```bash
docker compose up --build
```

This starts:

- MLflow tracking server: http://localhost:5000
- FastAPI service: http://localhost:8000
- Equipment health dashboard: http://localhost:8000
- FastAPI docs: http://localhost:8000/docs
- Dagster webserver: http://localhost:3000
- `training-init`, which downloads NASA C-MAPSS and executes the full Dagster job: dlt, dbt, tests, a genuinely executed training notebook, MLflow registration, and monitoring evidence.

For a direct local Python run:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/download_data.py
PYTHONPATH=src python orchestration/run_local.py
PYTHONPATH=src python scripts/execute_training_notebook.py
PYTHONPATH=src uvicorn industrial_health.api.app:app --host 0.0.0.0 --port 8000
```

Then test:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  --data @demo/predict_sample.json
```

## Final Training Proof

The final notebook was executed by a real Jupyter kernel and used the dbt/DuckDB output for all NASA C-MAPSS subsets FD001-FD004:

- raw training rows: 160,359
- raw test rows: 104,897
- training engines: 709
- test engines: 707
- final model: `HistGradientBoostingRegressor`
- standard final-cycle MAE: 12.5568
- standard final-cycle RMSE: 16.9251

Proof files:

- [`reports/model_metrics/final_evaluation.md`](reports/model_metrics/final_evaluation.md)
- [`reports/model_metrics/final_evaluation.json`](reports/model_metrics/final_evaluation.json)
- [`notebooks/training_executed.ipynb`](notebooks/training_executed.ipynb)
- [`docs/final-report/final-report.md`](docs/final-report/final-report.md)

## Target Architecture

```text
Raw sensor files / API
        |
        v
dlt ingestion
        |
        v
DuckDB raw and staging storage
        |
        v
dbt transformations and quality tests
        |
        v
Feature tables
        |
        v
Scikit-learn training pipeline
        |
        v
MLflow tracking and model registry
        |
        v
FastAPI prediction service
        |
        v
Docker, GitHub Actions, monitoring, and final demo
```

## Team Branches

Each member works in their own branch and opens pull requests into `main`.

| Member | GitHub | Branch | Main ownership |
|---|---|---|---|
| Ossama | `Maaskk` | `owner/Maaskk` |  MLOps integration, MLflow, serving, Docker, CI/CD, monitoring |
| Mohamed | `mohamed-kar1` | `feature/mohamed-kar1` | dlt, DuckDB, Dagster, pipeline automation |
| Hamza | `HamzaElhaddaji` | `feature/HamzaElhaddaji` | data contracts, tests, data lineage, documentation QA |
| Mouhcine | `Mouhcine005` | `feature/Mouhcine005` | model training, evaluation, feature engineering |
| Hajar | `HajarEnnajdy` | `feature/HajarEnnajdy` | API schemas, demo client, user-facing demo flow |
| Ilyass | pending | `feature/ilyass` | EDA, business analysis, KPIs, visual evidence |
| Akram | `Adonis-I` | `feature/Adonis-I` | Agile artifacts, sprint reports, final release and presentation |

Detailed task files are in [`team/`](team/).

## Minimum Deliverables

- Project vision and data strategy.
- Agile backlog with at least 3 sprints.
- dlt ingestion pipeline.
- DuckDB local analytical storage.
- dbt transformations and tests.
- Dagster orchestration.
- Data quality tests, data contract, data lineage.
- Scikit-learn model with training and evaluation.
- MLflow tracking, parameters, metrics, artifacts, and registry.
- FastAPI service exposing:
  - `GET /health`
  - `POST /predict`
- Docker containerization.
- GitHub Actions CI/CD. The active workflow is stored in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- Monitoring for service health, latency, ML metrics, and drift.
- Final report, demo, and presentation.

## Final Documentation

- API demo guide: [`docs/api.md`](docs/api.md)
- Monitoring: [`docs/monitoring.md`](docs/monitoring.md)
- Agile backlog and sprints: [`agile/`](agile/)
- Release checklist: [`docs/release-checklist.md`](docs/release-checklist.md)
- Safe form guidance: [`docs/group-form-info.md`](docs/group-form-info.md)

## Dataset and License

The dataset is the official NASA Turbofan Engine Degradation Simulation Data Set from the NASA Ames Prognostics Center of Excellence. Dataset source, citation, usage rules, and backup options are documented in [`docs/data-sources-and-licenses.md`](docs/data-sources-and-licenses.md).

This repository's code and documentation use the MIT License. The NASA dataset is not owned by this project and should not be committed into git.

## Independent Work Model

Each teammate has a branch, a task file, and primary folder ownership. Integration rules are documented in [`docs/team-integration-contracts.md`](docs/team-integration-contracts.md). The goal is that each person can work alone, open a pull request, and let Ossama merge after checking the shared contracts.

## Working Rules

1. Create one branch per person.
2. Never commit directly to `main` after initial setup.
3. Every pull request must include:
   - What changed.
   - How it was tested.
   - Screenshots or logs when relevant.
   - Link to the related task file.
4. Keep contracts stable between modules.
5. Use small pull requests so integration stays easy.
