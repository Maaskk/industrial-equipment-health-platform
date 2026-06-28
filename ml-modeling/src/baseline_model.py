"""
baseline_model.py
Baseline RUL regression using raw sensor readings only (no feature engineering).
Run: python src/baseline_model.py
"""

import json
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

from data_loader import load_dataset

RUL_CLIP = 125  # standard C-MAPSS convention, decided from train distribution only
SENSOR_COLS = [f"sensor_{i}" for i in range(1, 22)]
SETTING_COLS = ["op_setting_1", "op_setting_2", "op_setting_3"]
RAW_FEATURES = SETTING_COLS + SENSOR_COLS


def clip_rul(df, clip=RUL_CLIP):
    df = df.copy()
    df["RUL"] = df["RUL"].clip(upper=clip)
    return df


def evaluate(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return {"MAE": float(mae), "RMSE": float(rmse)}


def cross_validate(train_df, features, model_factory, n_splits=5):
    """GroupKFold CV split by unit -> no leakage across folds."""
    gkf = GroupKFold(n_splits=n_splits)
    groups = train_df["unit"]
    X = train_df[features].values
    y = train_df["RUL"].values

    fold_metrics = []
    for fold, (tr_idx, val_idx) in enumerate(gkf.split(X, y, groups=groups)):
        scaler = StandardScaler().fit(X[tr_idx])
        X_tr, X_val = scaler.transform(X[tr_idx]), scaler.transform(X[val_idx])

        model = model_factory()
        model.fit(X_tr, y[tr_idx])
        preds = model.predict(X_val)

        m = evaluate(y[val_idx], preds)
        m["fold"] = fold
        fold_metrics.append(m)

    return fold_metrics


def main():
    train, test = load_dataset("data/raw", "FD001")
    train = clip_rul(train)
    test = clip_rul(test)

    model_factory = lambda: RandomForestRegressor(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    )

    print("Running GroupKFold cross-validation (baseline, raw sensors)...")
    cv_metrics = cross_validate(train, RAW_FEATURES, model_factory)
    for m in cv_metrics:
        print(f"  Fold {m['fold']}: MAE={m['MAE']:.2f}  RMSE={m['RMSE']:.2f}")

    avg_mae = np.mean([m["MAE"] for m in cv_metrics])
    avg_rmse = np.mean([m["RMSE"] for m in cv_metrics])
    print(f"\nCV average: MAE={avg_mae:.2f}  RMSE={avg_rmse:.2f}")

    # Final fit on full train, evaluate on held-out NASA test set
    scaler = StandardScaler().fit(train[RAW_FEATURES].values)
    X_train = scaler.transform(train[RAW_FEATURES].values)
    X_test = scaler.transform(test[RAW_FEATURES].values)

    final_model = model_factory()
    final_model.fit(X_train, train["RUL"].values)
    test_preds = final_model.predict(X_test)
    test_metrics = evaluate(test["RUL"].values, test_preds)
    print(f"\nFinal TEST set metrics: MAE={test_metrics['MAE']:.2f}  RMSE={test_metrics['RMSE']:.2f}")

    # Save artifacts
    Path("models").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    joblib.dump({"model": final_model, "scaler": scaler, "features": RAW_FEATURES},
                "models/baseline_model.joblib")

    results = {
        "model": "RandomForestRegressor (baseline, raw sensors)",
        "features": RAW_FEATURES,
        "rul_clip": RUL_CLIP,
        "cv_metrics": cv_metrics,
        "cv_avg": {"MAE": avg_mae, "RMSE": avg_rmse},
        "test_metrics": test_metrics,
    }
    with open("reports/baseline_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nSaved model -> models/baseline_model.joblib")
    print("Saved results -> reports/baseline_results.json")


if __name__ == "__main__":
    main()