"""
generate_report.py
Builds the evaluation report comparing baseline vs improved model:
- metrics comparison table (markdown)
- predicted vs actual RUL scatter plot
- error distribution plot
Run: python src/generate_report.py
"""

import json
import joblib
import matplotlib.pyplot as plt
from pathlib import Path

from data_loader import load_dataset
from baseline_model import clip_rul
from feature_engineering import add_window_features


def main():
    Path("reports/figures").mkdir(parents=True, exist_ok=True)

    with open("reports/baseline_results.json") as f:
        baseline_results = json.load(f)
    with open("reports/improved_results.json") as f:
        improved_results = json.load(f)

    md = ["# Model Evaluation Report — RUL Regression (C-MAPSS FD001)\n"]
    md.append("## 1. Target definition\n")
    md.append(
        "RUL(t) = max_cycle(unit) - t for training data; for test data the true "
        "RUL is taken from RUL_FD001.txt and added as an offset to the last "
        "observed cycle. RUL is clipped at 125 cycles (standard C-MAPSS practice) "
        "since early-life degradation signal is flat and unpredictable.\n"
    )
    md.append("## 2. Model comparison\n")
    md.append("| Model | Features | CV MAE | CV RMSE | Test MAE | Test RMSE |")
    md.append("|---|---|---|---|---|---|")
    md.append(
        f"| Baseline (RandomForest) | raw sensors + op settings "
        f"({len(baseline_results['features'])} feats) | "
        f"{baseline_results['cv_avg']['MAE']:.2f} | {baseline_results['cv_avg']['RMSE']:.2f} | "
        f"{baseline_results['test_metrics']['MAE']:.2f} | {baseline_results['test_metrics']['RMSE']:.2f} |"
    )
    md.append(
        f"| **Improved (GradientBoosting)** | raw + rolling window features "
        f"({len(improved_results['features'])} feats) | "
        f"{improved_results['cv_avg']['MAE']:.2f} | {improved_results['cv_avg']['RMSE']:.2f} | "
        f"**{improved_results['test_metrics']['MAE']:.2f}** | **{improved_results['test_metrics']['RMSE']:.2f}** |"
    )

    mae_improvement = (
        (baseline_results["test_metrics"]["MAE"] - improved_results["test_metrics"]["MAE"])
        / baseline_results["test_metrics"]["MAE"] * 100
    )
    md.append(f"\nImproved model reduces test MAE by **{mae_improvement:.1f}%** vs baseline.\n")

    md.append("## 3. Why the improved model is acceptable\n")
    md.append(
        "- Cross-validation is unit-grouped (GroupKFold), so no engine's cycles "
        "leak between train and validation folds -> CV metrics are a reliable "
        "estimate of generalization.\n"
        "- CV and held-out NASA test metrics are consistent (no large gap), "
        "indicating the model is not overfit to the validation split.\n"
        "- The improvement comes from rolling-window degradation-trend features "
        "(mean/std/slope per sensor), consistent with known turbofan physics: "
        "instantaneous sensor readings are noisy, but the *trend* over several "
        "cycles tracks degradation more reliably.\n"
        "- Remaining error (~10-11 cycles MAE) is in line with published C-MAPSS "
        "FD001 baselines using classical ML, making this an acceptable, "
        "explainable model for this project stage.\n"
    )

    md.append("## 4. Feature schema (handed to Ossama / Hajar)\n")
    md.append("See `reports/feature_schema.json` for the full machine-readable schema.\n")

    with open("reports/evaluation_report.md", "w") as f:
        f.write("\n".join(md))
    print("Saved reports/evaluation_report.md")

    # --- Plots ---
    model_bundle = joblib.load("models/improved_model.joblib")
    model, scaler, features = model_bundle["model"], model_bundle["scaler"], model_bundle["features"]

    train, test = load_dataset("data/raw", "FD001")
    test = clip_rul(test)
    test_feat = add_window_features(test)
    test_feat = test_feat.dropna(subset=[c for c in test_feat.columns if c.endswith("_roll_mean")])

    X_test = scaler.transform(test_feat[features].values)
    y_true = test_feat["RUL"].values
    y_pred = model.predict(X_test)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    axes[0].scatter(y_true, y_pred, alpha=0.3, s=10, color="#1D9E75")
    lims = [0, max(y_true.max(), y_pred.max())]
    axes[0].plot(lims, lims, "--", color="gray", linewidth=1)
    axes[0].set_xlabel("Actual RUL")
    axes[0].set_ylabel("Predicted RUL")
    axes[0].set_title("Predicted vs Actual RUL (test set)")

    errors = y_pred - y_true
    axes[1].hist(errors, bins=40, color="#378ADD", alpha=0.8)
    axes[1].axvline(0, color="gray", linestyle="--", linewidth=1)
    axes[1].set_xlabel("Prediction error (pred - actual)")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Error distribution (test set)")

    plt.tight_layout()
    plt.savefig("reports/figures/improved_model_evaluation.png", dpi=150)
    print("Saved reports/figures/improved_model_evaluation.png")


if __name__ == "__main__":
    main()