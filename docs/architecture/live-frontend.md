# Live frontend architecture

The public application is hosted at `https://industrial-equipment-health-platfor.vercel.app/`.

Komodo manages the training pipeline, model registry, API, MLflow, and Dagster services on the shared server. The FastAPI service on port 3402 exposes application data, predictions, health information, and OpenAPI documentation. It does not provide a second user interface.

The Vercel application serves the existing browser interface. Its server-side routes forward application requests to the Komodo API. This keeps browser traffic on HTTPS while predictions are produced by the champion model loaded from MLflow.
