# Industrial Equipment Health Platform

## Delivery

The primary application is hosted on the university server at `http://exp.s3.fsbm.ma:3402/`. The same FastAPI process serves the existing dashboard and all product API routes. Komodo manages the five-service Compose Stack on shared Server `vh3`.

## DataOps

The verified chain is NASA C-MAPSS download with SHA-256 validation, dlt ingestion, DuckDB storage, three dbt models, 11 dbt tests, causal feature generation, model training, MLflow registration, and monitoring output. dlt and DuckDB paths are explicit, and CI starts from empty temporary state.

## Model

- Estimator: `HistGradientBoostingRegressor`
- Training subsets: FD001, FD002, FD003, FD004
- Features: 89
- Standard final-cycle test engines: 707
- MAE: 12.5568 cycles
- RMSE: 16.9251 cycles
- NASA asymmetric score: 4466.3383

Each training run stores metrics and `release_evaluation.json` in MLflow. A candidate receives the `champion` alias only when both final-cycle MAE and RMSE are no worse than the existing champion.

## Orchestration

Dagster exposes seven ordered assets: dlt ingestion, dbt transformation, dbt tests, staging validation, mart validation, training and registration, and drift reporting. `final_mlops_job` runs during initialization. `daily_schedule` is enabled by default for 06:00 Africa/Casablanca, with `dagster-daemon` executing schedules.

## Serving

The API loads the MLflow champion and validates requests against the 89-feature schema. The dashboard provides Fleet Overview, Engine Replay, operations and evaluation modes, Prediction Lab, CSV batch scoring, maintenance planning, platform evidence, monitoring, and project documentation.

## Release path

GitHub CI runs ingestion, transformations, tests, training, linting, Docker configuration, builds, smoke inference, and secret scanning. Production deployment has an explicit approval gate. The Komodo Stack deployment is followed by automated checks of the dashboard, health, docs, release SHA, registry source, and a prediction.

## Limitations

- C-MAPSS is simulation data, not live industrial telemetry.
- The Three.js engine is explanatory, not a physics simulator.
- Risk levels are thresholds on predicted RUL, not a separate calibrated classifier.
- The drift signal measures predicted-RUL mean shift only.
