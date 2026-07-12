"""
improved_model.py
Improved RUL regression using engineered lifecycle-window features
(rolling mean/std/slope per sensor) on top of raw sensors.
Run: python src/improved_model.py
"""

import json
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from data_loader import load_dataset
from feature_engineering import add_window_features, get_feature_columns
from baseline_model import clip_rul, evaluate, RUL_CLIP


def prepare(df, window=5):
    feat = add_window_features(df, window=window)
    feat = feat.dropna(subset=[c for c in feat.columns if c.endswith("_roll_mean")])
    return feat


def cross_validate(train_df, features, model_factory, n_splits=5):
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

    train_feat = prepare(train)
    test_feat = prepare(test)

    features = get_feature_columns(window_cols=True)
    features = [c for c in features if c in train_feat.columns]

    def model_factory():
        return GradientBoostingRegressor(
            n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42
        )

    print("Running GroupKFold cross-validation (improved, engineered features)...")
    cv_metrics = cross_validate(train_feat, features, model_factory)
    for m in cv_metrics:
        print(f"  Fold {m['fold']}: MAE={m['MAE']:.2f}  RMSE={m['RMSE']:.2f}")

    avg_mae = np.mean([m["MAE"] for m in cv_metrics])
    avg_rmse = np.mean([m["RMSE"] for m in cv_metrics])
    print(f"\nCV average: MAE={avg_mae:.2f}  RMSE={avg_rmse:.2f}")

    scaler = StandardScaler().fit(train_feat[features].values)
    X_train = scaler.transform(train_feat[features].values)
    X_test = scaler.transform(test_feat[features].values)

    final_model = model_factory()
    final_model.fit(X_train, train_feat["RUL"].values)
    test_preds = final_model.predict(X_test)
    test_metrics = evaluate(test_feat["RUL"].values, test_preds)
    print(f"\nFinal TEST set metrics: MAE={test_metrics['MAE']:.2f}  RMSE={test_metrics['RMSE']:.2f}")

    Path("models").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    joblib.dump({"model": final_model, "scaler": scaler, "features": features},
                "models/improved_model.joblib")

    results = {
        "model": "GradientBoostingRegressor (improved, engineered window features)",
        "features": features,
        "rul_clip": RUL_CLIP,
        "window_size": 5,
        "cv_metrics": cv_metrics,
        "cv_avg": {"MAE": avg_mae, "RMSE": avg_rmse},
        "test_metrics": test_metrics,
    }
    with open("reports/improved_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nSaved model -> models/improved_model.joblib")
    print("Saved results -> reports/improved_results.json")


if __name__ == "__main__":
    main()
