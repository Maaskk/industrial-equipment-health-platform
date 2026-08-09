# Live frontend architecture

The production application is hosted by the university deployment at `http://exp.s3.fsbm.ma:3402/`.

Komodo manages the complete Docker Compose workload on the shared server. FastAPI serves the existing dashboard, application API, health endpoint, and OpenAPI documentation from the same container on port 3402. Browser requests use same-origin relative routes.

MLflow and Dagster run on the internal Compose network. The `ops-gateway` service exposes their consoles on ports 3401 and 3403 with HTTP authentication. FastAPI accesses MLflow directly inside the Compose network, so protecting the console does not interrupt model loading or prediction.

This is the only production dashboard. No external frontend host is required.
