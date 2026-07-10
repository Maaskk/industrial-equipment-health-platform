# Final Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the scattered branch work into one reproducible local MLOps/DataOps project that runs with Docker Compose and has proof of training, serving, monitoring, and project management.

**Architecture:** Build `integration/final` from `main`, merge completed teammate branches, then make the final project runnable from one command. The final flow is NASA C-MAPSS data download/preparation, DuckDB/dbt/Dagster orchestration, sklearn training with MLflow tracking and registry artifacts, FastAPI serving the trained model, JSONL monitoring/drift reports, and CI gates.

**Tech Stack:** Python, dlt, DuckDB, dbt, Dagster, scikit-learn, MLflow, FastAPI, Docker Compose, GitHub Actions, Jupyter notebooks.

---

### Task 1: Branch Integration

**Files:**
- Merge from: `origin/feature/mohamed-kar1`
- Merge from: `origin/feature/HamzaElhaddaji`
- Merge from: `origin/feature/Mouhcine005`
- Merge from: `origin/owner/Maaskk`
- Merge from: `origin/feature/ilyass-analytics-eda`
- Create/modify: `docs/integration-status.md`

- [ ] **Step 1: Merge DataOps**

Run:
```bash
git merge --no-edit origin/feature/mohamed-kar1
```

Expected: DataOps files appear under `src/industrial_health/ingestion/`, `dbt_project/`, `orchestration/`, and `docs/dataops.md`.

- [ ] **Step 2: Merge contracts and quality docs**

Run:
```bash
git merge --no-edit origin/feature/HamzaElhaddaji
```

Expected: data contracts and data quality docs appear under `contracts/` and `docs/`.

- [ ] **Step 3: Merge ML modeling**

Run:
```bash
git merge --no-edit origin/feature/Mouhcine005
```

Expected: model training code and reports appear under `ml-modeling/`.

- [ ] **Step 4: Merge MLOps/API**

Run:
```bash
git merge --no-edit origin/owner/Maaskk
```

Expected: API, MLOps utilities, Docker files, monitoring docs, scripts, tests, and CI appear.

- [ ] **Step 5: Merge analytics notebook**

Run:
```bash
git merge --no-edit origin/feature/ilyass-analytics-eda
```

Expected: EDA notebook appears, then it is moved into the final notebook structure.

- [ ] **Step 6: Record branch status**

Create `docs/integration-status.md` with this structure:
```markdown
# Integration Status

## Merged Work

| Area | Branch | Status |
|---|---|---|
| DataOps | `feature/mohamed-kar1` | merged |
| Data contracts | `feature/HamzaElhaddaji` | merged |
| ML modeling | `feature/Mouhcine005` | merged |
| MLOps/API | `owner/Maaskk` | merged |
| Analytics | `feature/ilyass-analytics-eda` | merged |

## Rebuilt By Integration

- Hajar API/demo work was missing, so integration implements the API demo deliverables.
- Akram agile/release work was missing, so integration implements the release artifacts.
```

### Task 2: Reproducible Data And Training

**Files:**
- Modify/create: `scripts/download_data.py`
- Modify/create: `scripts/train_model.py`
- Modify/create: `notebooks/training_executed.ipynb`
- Modify/create: `models/latest/feature_schema.json`
- Modify/create: `models/latest/metrics.json`
- Modify/create: `models/latest/model.pkl`
- Modify/create: `reports/model_metrics/final_evaluation.json`
- Modify/create: `reports/model_metrics/final_evaluation.md`

- [ ] **Step 1: Add controlled data download**

Implement `scripts/download_data.py` so it downloads the NASA C-MAPSS zip to `data/raw/`, extracts FD001-FD004 text files, and refuses to redownload when files exist.

- [ ] **Step 2: Add final training script**

Implement `scripts/train_model.py` so it trains on FD001-FD004 when present, logs parameters/metrics/artifacts to local MLflow, saves a complete sklearn pipeline to `models/latest/model.pkl`, writes `feature_schema.json`, writes `metrics.json`, and writes Markdown/JSON reports.

- [ ] **Step 3: Add standard test evaluation**

The script must compute final-observed-row test metrics per engine, row-level online metrics, naive mean baseline, cycle-only baseline, Ridge baseline, RandomForest baseline, and GradientBoosting final model.

- [ ] **Step 4: Preserve proof notebook**

Create `notebooks/training_executed.ipynb` with executed cells showing dataset counts, model comparison, final metrics, artifact paths, and MLflow run id.

### Task 3: API, Demo, And No Silent Fake Model

**Files:**
- Modify: `src/industrial_health/api/app.py`
- Modify: `src/industrial_health/mlops/model_loader.py`
- Create/modify: `docs/api.md`
- Create/modify: `demo/predict_sample.json`
- Create/modify: `scripts/smoke_predict.py`

- [ ] **Step 1: Disable fallback by default**

Make fallback model usage require `ALLOW_FALLBACK_MODEL=true`; otherwise missing `models/latest/model.pkl` must fail readiness and API startup.

- [ ] **Step 2: Validate feature schema**

Load `models/latest/feature_schema.json` and reject missing or unknown feature fields in `/predict`.

- [ ] **Step 3: Improve `/health`**

Return readiness fields for `model_loaded`, `model_source`, `model_version`, `feature_count`, `mlflow_tracking_uri`, and `monitoring_log_path`.

- [ ] **Step 4: Add demo payload and docs**

Create one valid sample payload and document `GET /health`, `POST /predict`, expected errors, and curl examples.

### Task 4: Docker Compose And CI

**Files:**
- Modify: `Dockerfile`
- Modify: `docker-compose.yml`
- Modify: `.github/workflows/ci.yml`
- Create/modify: `scripts/check_readiness.py`

- [ ] **Step 1: Compose services**

Compose must include at minimum `mlflow`, `api`, `dagster-webserver`, `dagster-daemon`, and an executable training/init path.

- [ ] **Step 2: One-command local run**

`docker compose up --build` must create or reuse model artifacts, start API, start MLflow, and expose a working health endpoint.

- [ ] **Step 3: CI gates**

GitHub Actions must run Python tests, compile checks, `docker compose config`, Docker build, and an API smoke path when Docker is available.

### Task 5: Agile, Release, Monitoring, And Form Guidance

**Files:**
- Create/modify: `agile/product-backlog.md`
- Create/modify: `agile/sprint-plan.md`
- Create/modify: `agile/sprint-review-retro.md`
- Create/modify: `docs/final-report/final-report.md`
- Create/modify: `docs/release-checklist.md`
- Create/modify: `docs/group-form-info.md`
- Create/modify: `docs/monitoring.md`

- [ ] **Step 1: Rebuild missing Akram deliverables**

Create product backlog, user stories, three-sprint plan, review notes, retrospective notes, and release checklist.

- [ ] **Step 2: Rebuild missing Hajar deliverables**

Create API/demo docs, payload examples, error examples, and a demo rehearsal script.

- [ ] **Step 3: Fill non-sensitive form guidance**

Create `docs/group-form-info.md` with project name, group name recommendation, GitHub repo URL, and safe username rules. Do not include or invent passwords.

- [ ] **Step 4: Monitoring proof**

Document prediction logging, latency, error-rate expectations, drift report command, and where generated reports are stored.

### Task 6: Verification

**Files:**
- Inspect current tree, generated reports, Docker output, CI workflow, and API response.

- [ ] **Step 1: Run unit tests**

Run:
```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [ ] **Step 2: Run compile check**

Run:
```bash
PYTHONPATH=src python -m compileall src tests scripts orchestration ml-modeling
```

Expected: command exits 0.

- [ ] **Step 3: Run readiness**

Run:
```bash
PYTHONPATH=src python scripts/check_readiness.py
```

Expected: all non-cloud local readiness checks pass.

- [ ] **Step 4: Run Docker verification**

Run:
```bash
docker compose config
docker compose build
docker compose up -d
curl -f http://localhost:8000/health
PYTHONPATH=src python scripts/smoke_predict.py
docker compose down
```

Expected: Docker daemon is running and each command exits 0.

- [ ] **Step 5: Push integration branch**

Run:
```bash
git push -u origin integration/final
```

Expected: branch is available for final pull request into `main`.

---

## Self-Review

- The plan covers branch integration, reproducible training, MLflow artifacts, API hardening, Docker Compose, CI, monitoring, missing Hajar/Akram deliverables, form guidance, and verification.
- The plan intentionally avoids submitting Google Forms or storing passwords.
- Completion requires evidence from commands, generated artifacts, and GitHub branch state.
