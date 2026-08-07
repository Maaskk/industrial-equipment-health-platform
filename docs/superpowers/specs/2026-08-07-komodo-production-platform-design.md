# Komodo production platform design

The production path has one source of truth: this GitHub repository. The existing GitHub Actions workflow validates every change. Komodo builds the application image on the connected Docker host, syncs `komodo/resources.toml`, deploys `deploy/compose.production.yml`, monitors the host and stack, and runs a scheduled health audit.

The long-running services are the prediction API, MLflow, Dagster webserver, and Dagster daemon. `training-init` downloads the NASA C-MAPSS subset and creates the registered model before dependent services start. Komodo excludes that successful one-shot container from stack health.

All service data uses named Docker volumes. Only ports 3000, 5000, and 8000 are published, bound to localhost. The Docker host reports CPU, memory, disk, reachability, and version alerts to Komodo.

Deployment automation consists of the existing GitHub validation workflow plus a Komodo Repo, Build, Stack, Procedure, Action, Resource Sync, and scheduled executions. The Resource Sync also grants `oashad` write access to the project resources after an administrator applies the first sync.
