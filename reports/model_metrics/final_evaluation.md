# Final Model Evaluation

The final model trains on NASA C-MAPSS FD001-FD004 when all files are present.
The primary score is the standard final-observed-cycle test evaluation per engine.

## Final Model

- Model: HistGradientBoostingRegressor
- Feature count: 89
- Train rows after rolling warm-up: 157523
- Online test rows after rolling warm-up: 102069
- Final-cycle test engines: 707

## Standard Final-Cycle Metrics

- MAE: 12.5568
- RMSE: 16.9251
- NASA asymmetric score: 4466.3383

## Online Row-Level Metrics

- MAE: 10.1897
- RMSE: 15.7379
- NASA asymmetric score: 781814.2132

## Honest Limitations

- NASA C-MAPSS is simulated data, not real factory telemetry.
- Risk level is derived from predicted RUL thresholds, not a calibrated classifier.
- The final-cycle metric is the defensible benchmark metric; online row-level metrics are secondary.
