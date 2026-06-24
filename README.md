# Industrial Equipment Health Platform

Predictive maintenance MLOps project for industrial turbofan sensor data.

This repository is designed for the MLOps & DataOps final project. The goal is not only to train a model, but to industrialize the full lifecycle of a data product: ingestion, storage, transformation, quality, orchestration, model training, tracking, serving, CI/CD, monitoring, and documentation.

## Project Choice

Selected subject from the official list:

**Project 7 - Maintenance predictive industrielle**

Product framing:

**Industrial Equipment Health Platform: Predictive Maintenance with MLOps and DataOps**

The platform predicts equipment degradation risk and remaining useful life from multivariate sensor readings. The recommended dataset is NASA C-MAPSS turbofan degradation data or a compatible public predictive-maintenance dataset.

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
| Ossama | `Maaskk` | `owner/Maaskk-mlops-integration` | Hardest role: MLOps integration, MLflow, serving, Docker, CI/CD, monitoring |
| Mohamed | `mohamed-kar1` | `feature/mohamed-kar1-dataops-infra` | dlt, DuckDB, Dagster, pipeline automation |
| Hamza | `HamzaElhaddaji` | `feature/HamzaElhaddaji-quality-docs` | data contracts, tests, data lineage, documentation QA |
| Mouhcine | `Mouhcine005` | `feature/Mouhcine005-ml-modeling` | model training, evaluation, feature engineering |
| Hajar | `HajarEnnajdy` | `feature/HajarEnnajdy-api-demo` | API schemas, demo client, user-facing demo flow |
| Ilyass | pending | `feature/ilyass-analytics-eda` | EDA, business analysis, KPIs, visual evidence |
| Akram | `Adonis-I` | `feature/Adonis-I-agile-release` | Agile artifacts, sprint reports, final release and presentation |

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
- GitHub Actions CI/CD. The template is stored in [`docs/ci/github-actions-template.yml`](docs/ci/github-actions-template.yml) because the current publishing credential cannot push active workflow files without GitHub's `workflow` scope.
- Monitoring for service health, latency, ML metrics, and drift.
- Final report, demo, and presentation.

## Dataset and License

The recommended dataset is the official NASA Turbofan Engine Degradation Simulation Data Set from the NASA Ames Prognostics Center of Excellence. Dataset source, citation, usage rules, and backup options are documented in [`docs/data-sources-and-licenses.md`](docs/data-sources-and-licenses.md).

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
