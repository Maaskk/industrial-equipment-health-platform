# Project Charter

## Problem

Industrial equipment failures are expensive, unsafe, and difficult to anticipate when maintenance is scheduled only by fixed intervals. Sensor data can reveal early degradation patterns before a failure happens.

## Objective

Build an industrial predictive-maintenance data product that predicts equipment health from sensor measurements and exposes the prediction through a production-style API.

## Target Users

- Maintenance engineers who need failure-risk alerts.
- Operations managers who need fleet-level reliability indicators.
- Data and ML teams who need a reproducible pipeline.

## Business Value

- Reduce unplanned downtime.
- Improve maintenance planning.
- Provide transparent model metrics and reproducible decisions.
- Demonstrate a complete MLOps and DataOps lifecycle.

## Data Strategy

- Use a public predictive-maintenance dataset, preferably NASA C-MAPSS turbofan degradation data.
- Store raw ingested data separately from cleaned and feature-ready tables.
- Define data contracts for required sensor columns, valid ranges, freshness, and completeness.
- Track lineage from raw files to model predictions.

## Success Criteria

- A new team member can run the project from README instructions.
- The pipeline can rebuild the feature table from raw data.
- At least one trained model is tracked in MLflow with parameters, metrics, and artifacts.
- The model is served through FastAPI with `GET /health` and `POST /predict`.
- CI validates code, data contracts, tests, and Docker build.
- Monitoring captures service availability, latency, basic prediction logs, and drift indicators.

