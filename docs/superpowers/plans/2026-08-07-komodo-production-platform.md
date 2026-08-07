# Komodo production implementation plan

1. Validate the production Compose and declarative Komodo resource contracts.
2. Build the application image on the connected Komodo Docker host with commit and `latest` tags.
3. Onboard the Docker Desktop host as `oussama-macbook` with a Builder.
4. Bootstrap `industrial-health-resources` from `komodo/resources.toml` and apply its diff.
5. Configure GitHub webhooks for Resource Sync and Stack deployment.
6. Deploy the stack and verify API, MLflow, Dagster, container state, schedules, and alerts.
