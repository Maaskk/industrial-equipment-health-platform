# Ossama - MLOps Integration Lead

GitHub: `Maaskk`

Branch: `owner/Maaskk`

## Mission

Make the project work end to end like a real industrial MLOps product.

You own the integration layer: MLflow, model registry, Docker, CI/CD, and the
connection between the data, model, API, and Komodo deployment.

## Main Deliverables

- MLflow tracking server setup and experiment conventions. See `docs/mlflow-model-registry.md`.
- Model registry workflow: register, stage, load, and serve a model version.
- FastAPI integration structure with Hajar:
  - `GET /health`
  - `POST /predict`
- Docker and Docker Compose architecture.
- GitHub Actions CI/CD template.
- End-to-end integration script or demo command. See `docs/demo-checklist.md`.
- Candidate evaluation and safe champion promotion.
- Scheduled training configuration with Dagster.
- Monitoring architecture and handoff to Aya for final evidence review.

## Inputs Needed From Others

- Mohamed: stable feature table location and pipeline command.
- Hamza: data contract and quality checks.
- Mouhcine: trained model artifact and expected feature schema.
- Hajar: API request/response schema and demo flow.
- Ilyass: business KPIs and sample cases for demo.
- Akram: sprint and presentation schedule.

## Acceptance Criteria

- A reviewer can run the service locally with one documented command.
- MLflow contains at least two tracked experiments with parameters, metrics, and artifacts.
- The API returns healthy status and valid predictions.
- Docker build passes.
- GitHub Actions runs lint and tests.
- Monitoring records latency and prediction logs for Aya's final review.
- The final demo works from a fresh clone.

## First Tasks

1. Define the repo execution contract in the README.
2. Create MLflow experiment naming conventions.
3. Design Docker Compose services.
4. Add CI skeleton and quality gates.
5. Coordinate API/model/data contracts before Sprint 2 ends.
