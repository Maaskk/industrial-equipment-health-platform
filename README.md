# Industrial Equipment Health Platform

Predictive-maintenance platform built around NASA C-MAPSS turbofan data. It covers ingestion, transformation, data checks, model training, experiment tracking, serving and monitoring in one local Docker stack.

## Team

<table>
  <tr>
    <td align="center"><a href="https://github.com/Maaskk"><img src="https://github.com/Maaskk.png?size=96" width="72" alt="Ossama"><br><sub><b>Ossama</b></sub></a></td>
    <td align="center"><a href="https://github.com/mohamed-kar1"><img src="https://github.com/mohamed-kar1.png?size=96" width="72" alt="Mohamed"><br><sub><b>Mohamed</b></sub></a></td>
    <td align="center"><a href="https://github.com/HamzaElhaddaji"><img src="https://github.com/HamzaElhaddaji.png?size=96" width="72" alt="Hamza"><br><sub><b>Hamza</b></sub></a></td>
    <td align="center"><a href="https://github.com/Mouhcine005"><img src="https://github.com/Mouhcine005.png?size=96" width="72" alt="Mouhcine"><br><sub><b>Mouhcine</b></sub></a></td>
    <td align="center"><a href="https://github.com/HajarEnnajdy"><img src="https://github.com/HajarEnnajdy.png?size=96" width="72" alt="Hajar"><br><sub><b>Hajar</b></sub></a></td>
    <td align="center"><a href="https://github.com/Iliassouchida"><img src="https://github.com/Iliassouchida.png?size=96" width="72" alt="Ilyass"><br><sub><b>Ilyass</b></sub></a></td>
    <td align="center"><a href="https://github.com/Adonis-I"><img src="https://github.com/Adonis-I.png?size=96" width="72" alt="Akram"><br><sub><b>Akram</b></sub></a></td>
  </tr>
</table>

Individual areas and accepted contributions are recorded in [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Run locally

```bash
docker compose up --build
```

This starts:

| Service | URL |
| --- | --- |
| Equipment dashboard and API | <http://localhost:8000> |
| FastAPI documentation | <http://localhost:8000/docs> |
| MLflow | <http://localhost:5000> |
| Dagster | <http://localhost:3000> |

`training-init` downloads C-MAPSS and runs the local Dagster job through ingestion, dbt, tests, notebook execution, MLflow registration and monitoring evidence.

Direct Python run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/download_data.py
PYTHONPATH=src python orchestration/run_local.py
PYTHONPATH=src python scripts/execute_training_notebook.py
PYTHONPATH=src uvicorn industrial_health.api.app:app --host 0.0.0.0 --port 8000
```

## Final model

The executed notebook trains on C-MAPSS subsets FD001 through FD004.

| Item | Result |
| --- | ---: |
| Training rows | 160,359 |
| Test rows | 104,897 |
| Training engines | 709 |
| Test engines | 707 |
| Model | HistGradientBoostingRegressor |
| Final-cycle MAE | 12.5568 |
| Final-cycle RMSE | 16.9251 |

Evidence is stored in [`reports/model_metrics/final_evaluation.md`](reports/model_metrics/final_evaluation.md), [`reports/model_metrics/final_evaluation.json`](reports/model_metrics/final_evaluation.json) and [`notebooks/training_executed.ipynb`](notebooks/training_executed.ipynb).

## Architecture

```text
C-MAPSS files
      |
     dlt
      |
   DuckDB
      |
 dbt + checks
      |
 feature tables
      |
 scikit-learn
      |
    MLflow
      |
   FastAPI
```

Dagster coordinates the pipeline. Docker Compose supplies the local runtime, and GitHub Actions runs the repository checks.

## Documentation

- [API guide](docs/api.md)
- [Monitoring](docs/monitoring.md)
- [Data sources and licences](docs/data-sources-and-licenses.md)
- [Team integration contracts](docs/team-integration-contracts.md)
- [Final report](docs/final-report/final-report.md)

The code and project documentation use the MIT License. NASA owns the C-MAPSS dataset, which is downloaded at runtime and is not committed to this repository.
