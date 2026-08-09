# Operations

## Persistent data

The production Compose file uses named volumes for NASA data, models, logs, reports, DuckDB, Dagster state, and MLflow state. Do not run `docker compose down -v` in production.

## Backup

Run from an authorized Server terminal during a quiet period:

```bash
docker run --rm \
  -v industrial-equipment-health-platform_mlflow-storage:/source:ro \
  -v "$PWD/backups":/backup \
  alpine tar czf /backup/mlflow-storage.tgz -C /source .
```

Repeat for `warehouse`, `models`, `reports`, `logs`, `data`, and `dagster-storage`. Store the archives outside the Docker host and record the release tag.

## Restore

Stop the Stack, keep the named volumes, restore one archive into its matching volume, and redeploy the same release tag. Verify `/health`, the MLflow champion alias, the Dagster run history, and one prediction before reopening the service.

## Logs

Use Komodo Stack service logs for active containers. Prediction records are retained in the `logs` volume. Request responses carry `X-Request-ID` so a browser request can be matched to application logs when request logging is enabled by the host.
