# Model Evaluation Report — RUL Regression (C-MAPSS FD001)

## 1. Target definition

RUL(t) = max_cycle(unit) - t for training data; for test data the true RUL is taken from RUL_FD001.txt and added as an offset to the last observed cycle. RUL is clipped at 125 cycles (standard C-MAPSS practice) since early-life degradation signal is flat and unpredictable.

## 2. Model comparison

| Model | Features | CV MAE | CV RMSE | Test MAE | Test RMSE |
|---|---|---|---|---|---|
| Baseline (RandomForest) | raw sensors + op settings (24 feats) | 13.51 | 18.40 | 12.43 | 17.12 |
| **Improved (GradientBoosting)** | raw + rolling window features (88 feats) | 11.50 | 16.35 | **10.47** | **15.70** |

Improved model reduces test MAE by **15.8%** vs baseline.

## 3. Why the improved model is acceptable

- Cross-validation is unit-grouped (GroupKFold), so no engine's cycles leak between train and validation folds -> CV metrics are a reliable estimate of generalization.
- CV and held-out NASA test metrics are consistent (no large gap), indicating the model is not overfit to the validation split.
- The improvement comes from rolling-window degradation-trend features (mean/std/slope per sensor), consistent with known turbofan physics: instantaneous sensor readings are noisy, but the *trend* over several cycles tracks degradation more reliably.
- Remaining error (~10-11 cycles MAE) is in line with published C-MAPSS FD001 baselines using classical ML, making this an acceptable, explainable model for this project stage.

## 4. Feature schema (handed to Ossama / Hajar)

See `reports/feature_schema.json` for the full machine-readable schema.
