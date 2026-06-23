# Ossama - MLOps Integration Lead

GitHub: `Maaskk`

Branch: `owner/Maaskk-mlops-integration`

Difficulty: **hardest role**

## Why this role fits

Public GitHub history shows strong signals in Python ML, RAG/vector search, GNN optimization, Kafka/Flink pipelines, ML apps, and TypeScript applications. This is the best match for the hardest role because it requires connecting data engineering, ML, API serving, DevOps, and monitoring into one working system.

## Mission

Make the project work end to end like a real industrial MLOps product.

You own the integration layer: MLflow, model registry, FastAPI deployment architecture, Docker, CI/CD, monitoring, and final demo reliability.

## Main Deliverables

- MLflow tracking server setup and experiment conventions. See `docs/mlflow-model-registry.md`.
- Model registry workflow: register, stage, load, and serve a model version.
- FastAPI integration structure with Hajar:
  - `GET /health`
  - `POST /predict`
- Docker and Docker Compose architecture.
- GitHub Actions CI/CD template.
- End-to-end integration script or demo command. See `docs/demo-checklist.md`.
- Monitoring design for:
  - service availability
  - response time
  - prediction logs
  - simple input drift
  - model metric tracking
- Final demo checklist.

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
- Monitoring records at least latency and prediction logs.
- The final demo works from a fresh clone.

## First Tasks

1. Define the repo execution contract in the README.
2. Create MLflow experiment naming conventions.
3. Design Docker Compose services.
4. Add CI skeleton and quality gates.
5. Coordinate API/model/data contracts before Sprint 2 ends.
