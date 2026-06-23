# Mouhcine - ML Modeling and Evaluation Lead

GitHub: `Mouhcine005`

Branch: `feature/Mouhcine005-ml-modeling`

## Why this role fits

Public GitHub history shows strong data and ML signals: real-time data pipelines, food outbreak severity ML, sales DataOps, student data cleaning, and multiple Python projects. This makes Mouhcine a strong fit for model development.

## Mission

Build the predictive-maintenance model and produce clear evaluation evidence.

## Main Deliverables

- Baseline model using scikit-learn.
- Improved model using engineered sensor features.
- Feature engineering logic for lifecycle windows.
- Train/test split strategy that avoids leakage.
- Evaluation report:
  - MAE/RMSE for remaining useful life regression, or
  - F1/ROC-AUC for failure-risk classification
- Model artifact ready for MLflow.
- Feature schema handed to Ossama and Hajar.

## Acceptance Criteria

- Model training is reproducible from a documented command.
- Metrics are saved and logged to MLflow with Ossama.
- Feature schema is stable and documented.
- Evaluation explains why the selected model is acceptable.
- At least one baseline is compared with one improved model.

## First Tasks

1. Review NASA C-MAPSS target definition.
2. Build a simple baseline.
3. Add feature windows and degradation labels.
4. Compare model metrics.
5. Package the best model for registry.
