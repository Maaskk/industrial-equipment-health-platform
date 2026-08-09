# Release Checklist

Canonical tag: `professor-demo-v1`

## Code and evidence

- [ ] Final commit is on `main` and `production`.
- [ ] `professor-demo-v1` points to the approved release.
- [ ] CI quality and secret jobs pass on that commit.
- [ ] `reports/release/final_release.json` and `.md` identify the release and champion.
- [ ] Full FD001 through FD004 metrics are preserved.

## Verification

```bash
python scripts/download_data.py
python orchestration/run_local.py
python scripts/train_model.py
python -m unittest discover -s tests -p 'test_*.py'
python -m pytest tests/test_dataops.py
ruff check .
docker compose config
docker compose -f deploy/compose.production.yml config
```

## Production

- [ ] Komodo Server `vh3` is `Ok`.
- [ ] Stack `industrial_equipment_health_platform` is running.
- [ ] Running service states match the five-service Compose definition.
- [ ] `/health` reports `mlflow_registry`, the champion version, release SHA, and release tag.
- [ ] Dashboard, docs, single prediction, batch prediction, maintenance plan, and monitoring routes pass.
- [ ] Dagster schedule is enabled and the daemon heartbeat is current.
- [ ] MLflow run, release evaluation artifact, model version, and champion alias agree with the release report.

Raw NASA files, credentials, API keys, and runtime volumes must remain outside git.
