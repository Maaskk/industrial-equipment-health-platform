# Release Checklist

Release branch: `integration/final`

Repository: https://github.com/Maaskk/industrial-equipment-health-platform

## Required Checks

| Check | Command or evidence | Status |
|---|---|---|
| Python unit tests | `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"` | pass locally |
| DataOps pytest checks | `PYTHONPATH=src python -m pytest tests/test_dataops.py` | pass locally after ingestion |
| dbt run/test | `PYTHONPATH=src python orchestration/run_local.py` | pass locally |
| Training proof | `PYTHONPATH=src python scripts/train_model.py --download` | pass locally on FD001-FD004 |
| Readiness | `PYTHONPATH=src python scripts/check_readiness.py` | pass locally |
| API sample prediction | `PYTHONPATH=src python scripts/smoke_predict.py` with API running | required before demo |
| Drift report | `PYTHONPATH=src python scripts/generate_drift_report.py` | required before demo |
| Docker config | `docker compose config` | required before merge |
| Docker build | `docker compose build` | required before merge |
| One-command local stack | `docker compose up --build` | required before final presentation |

## Artifacts To Show

- `reports/model_metrics/final_evaluation.md`
- `reports/model_metrics/final_evaluation.json`
- `reports/model_metrics/figures/final_model_comparison.png`
- `notebooks/training_executed.ipynb`
- `demo/predict_sample.json`
- `reports/monitoring/drift_report.json`
- GitHub Actions run for `.github/workflows/ci.yml`

## Release Rules

- Do not commit raw NASA data files.
- Do not submit or store Google Form passwords in the repo.
- Do not merge to `main` until Docker and API smoke pass.
- Demo must use `model_source: local_pickle`; `fallback` is test-only.
