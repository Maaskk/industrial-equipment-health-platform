# ML Modeling — Predictive Maintenance (C-MAPSS RUL Regression)

Owner: Mouhcine — model training, evaluation, feature engineering.

## Setup

Activate the project's existing `.venv` (see repo root), then:

```bash
pip install pandas scikit-learn matplotlib joblib mlflow
```

Place NASA C-MAPSS files (`train_FD001.txt`, `test_FD001.txt`, `RUL_FD001.txt`, ...)
into `data/raw/`. (Not committed to git — see `.gitignore`. Download from:
https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip)

## Reproduce everything (run in order, from ml-modeling/ as working directory)

```bash
python src/data_loader.py          # 1. sanity check data loading + RUL labeling
python src/baseline_model.py       # 2. baseline model (raw sensors only)
python src/feature_engineering.py  # 3. feature engineering sanity check
python src/improved_model.py       # 4. improved model (engineered window features)
python src/generate_report.py      # 5. build evaluation report + plots
python src/package_for_mlflow.py   # 6. package for MLflow registry
```

## Outputs

- `models/baseline_model.joblib`, `models/improved_model.joblib` — trained models + scaler + feature list
- `reports/baseline_results.json`, `reports/improved_results.json` — metrics
- `reports/evaluation_report.md` — full evaluation writeup
- `reports/figures/improved_model_evaluation.png` — pred-vs-actual + error distribution
- `reports/feature_schema.json` — feature schema handoff for Ossama (MLflow) / Hajar (API)
- `reports/leakage_strategy.md` — train/test split & leakage-avoidance documentation

## Method summary

- **Target**: RUL(t) = max_cycle(unit) − t, clipped at 125 cycles.
- **Validation**: GroupKFold(5) split by engine `unit` — no cycle leakage across folds.
- **Baseline**: RandomForestRegressor on raw sensors + op settings.
- **Improved**: GradientBoostingRegressor on raw features + rolling (window=5)
  mean/std/slope per sensor, computed causally per unit.
- **Result (FD001 test set)**: baseline MAE 12.43 / RMSE 17.12 →
  improved MAE 10.47 / RMSE 15.70 (~16% MAE reduction).

## Next steps (not yet done — flag in standup)

- Extend to FD002/FD003/FD004 (multiple operating conditions / fault modes —
  will likely need per-condition normalization).
- Try LSTM/sequence model as a stretch goal once classical baseline is locked in MLflow.
- Hyperparameter tuning (currently sane defaults, not grid-searched).