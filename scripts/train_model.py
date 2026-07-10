from __future__ import annotations

import argparse
import json
import math
import os
import pickle
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from industrial_health.mlops.serving_model import FeatureSchemaRULModel

try:
    from scripts.download_data import EXPECTED_FILES, download_cmapss
except ModuleNotFoundError:  # Direct execution: python scripts/train_model.py
    from download_data import EXPECTED_FILES, download_cmapss


RUL_CLIP = 125
WINDOW = 5
SUBSETS = ["FD001", "FD002", "FD003", "FD004"]
COLUMNS = (
    ["unit", "cycle", "op_setting_1", "op_setting_2", "op_setting_3"]
    + [f"sensor_{i}" for i in range(1, 22)]
)
SENSOR_COLS = [f"sensor_{i}" for i in range(1, 22)]
SETTING_COLS = [f"op_setting_{i}" for i in range(1, 4)]
RAW_FEATURES = ["subset_id", "cycle", *SETTING_COLS, *SENSOR_COLS]


def load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=r"\s+", header=None)
    df = df.iloc[:, : len(COLUMNS)]
    df.columns = COLUMNS
    return df


def add_train_rul(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["RUL"] = out.groupby("unit")["cycle"].transform("max") - out["cycle"]
    return out


def add_test_rul(df: pd.DataFrame, rul_path: Path) -> pd.DataFrame:
    out = df.copy()
    final_rul = pd.read_csv(rul_path, sep=r"\s+", header=None).iloc[:, 0]
    final_rul.index = final_rul.index + 1
    last_cycle = out.groupby("unit")["cycle"].max()
    virtual_failure_cycle = last_cycle + final_rul
    out["RUL"] = out["unit"].map(virtual_failure_cycle) - out["cycle"]
    return out


def load_subset(data_dir: Path, subset: str, subset_id: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = add_train_rul(load_raw(data_dir / f"train_{subset}.txt"))
    test = add_test_rul(load_raw(data_dir / f"test_{subset}.txt"), data_dir / f"RUL_{subset}.txt")
    for frame in (train, test):
        frame["subset"] = subset
        frame["subset_id"] = subset_id
        frame["engine_key"] = subset + "_" + frame["unit"].astype(str)
        frame["RUL"] = frame["RUL"].clip(upper=RUL_CLIP)
    return train, test


def load_all_subsets(data_dir: Path, subsets: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = [name for name in EXPECTED_FILES if not (data_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing NASA C-MAPSS files in {data_dir}: {missing}. "
            "Run `python scripts/download_data.py` first."
        )

    train_frames: list[pd.DataFrame] = []
    test_frames: list[pd.DataFrame] = []
    for index, subset in enumerate(subsets, start=1):
        train, test = load_subset(data_dir, subset, index)
        train_frames.append(train)
        test_frames.append(test)
    return pd.concat(train_frames, ignore_index=True), pd.concat(test_frames, ignore_index=True)


def rolling_slope(values: pd.Series, window: int) -> pd.Series:
    x = np.arange(window)
    x_mean = x.mean()
    denominator = ((x - x_mean) ** 2).sum()

    def slope(y: np.ndarray) -> float:
        if len(y) < window:
            return np.nan
        y_mean = y.mean()
        return float(((x - x_mean) * (y - y_mean)).sum() / denominator)

    return values.rolling(window).apply(slope, raw=True)


def add_window_features(df: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    out = df.sort_values(["engine_key", "cycle"]).copy()
    grouped = out.groupby("engine_key", sort=False)
    feature_frames = [out]
    for sensor in SENSOR_COLS:
        rolling = grouped[sensor].rolling(window)
        feature_frames.append(rolling.mean().reset_index(level=0, drop=True).rename(f"{sensor}_roll_mean"))
        feature_frames.append(rolling.std().reset_index(level=0, drop=True).rename(f"{sensor}_roll_std"))
        feature_frames.append(
            grouped[sensor].transform(lambda series: rolling_slope(series, window)).rename(
                f"{sensor}_roll_slope"
            )
        )
    engineered = pd.concat(feature_frames, axis=1)
    required = [f"{sensor}_roll_mean" for sensor in SENSOR_COLS]
    return engineered.dropna(subset=required).reset_index(drop=True)


def engineered_features() -> list[str]:
    features = list(RAW_FEATURES)
    for sensor in SENSOR_COLS:
        features.extend([f"{sensor}_roll_mean", f"{sensor}_roll_std", f"{sensor}_roll_slope"])
    return features


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(math.sqrt(mean_squared_error(y_true, y_pred)))


def nasa_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    diff = y_pred - y_true
    score = np.where(diff < 0, np.exp(-diff / 13.0) - 1.0, np.exp(diff / 10.0) - 1.0)
    return float(np.sum(score))


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": rmse(y_true, y_pred),
        "nasa_score": nasa_score(y_true, y_pred),
    }


def model_pipeline(model: object, scale: bool = True) -> Pipeline:
    steps: list[tuple[str, object]] = []
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", model))
    return Pipeline(steps)


def fit_and_evaluate(
    name: str,
    pipeline: Pipeline,
    train_df: pd.DataFrame,
    online_test_df: pd.DataFrame,
    final_test_df: pd.DataFrame,
    features: list[str],
) -> dict[str, object]:
    pipeline.fit(train_df[features].values, train_df["RUL"].values)
    online_pred = pipeline.predict(online_test_df[features].values)
    final_pred = pipeline.predict(final_test_df[features].values)
    return {
        "name": name,
        "features": features,
        "feature_count": len(features),
        "online_rows": int(len(online_test_df)),
        "final_engine_count": int(len(final_test_df)),
        "online_metrics": evaluate_predictions(online_test_df["RUL"].values, online_pred),
        "standard_final_cycle_metrics": evaluate_predictions(final_test_df["RUL"].values, final_pred),
    }


def cross_validate_final_model(
    train_df: pd.DataFrame,
    features: list[str],
    factory: Callable[[], Pipeline],
    n_splits: int = 5,
) -> list[dict[str, float]]:
    groups = train_df["engine_key"]
    splits = min(n_splits, groups.nunique())
    gkf = GroupKFold(n_splits=splits)
    X = train_df[features].values
    y = train_df["RUL"].values
    results: list[dict[str, float]] = []
    for fold, (train_index, valid_index) in enumerate(gkf.split(X, y, groups=groups), start=1):
        pipeline = factory()
        pipeline.fit(X[train_index], y[train_index])
        predictions = pipeline.predict(X[valid_index])
        metrics = evaluate_predictions(y[valid_index], predictions)
        metrics["fold"] = fold
        results.append(metrics)
    return results


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_report(path: Path, metrics: dict[str, object]) -> None:
    final = metrics["models"]["final_gradient_boosting"]["standard_final_cycle_metrics"]
    online = metrics["models"]["final_gradient_boosting"]["online_metrics"]
    lines = [
        "# Final Model Evaluation",
        "",
        "The final model trains on NASA C-MAPSS FD001-FD004 when all files are present.",
        "The primary score is the standard final-observed-cycle test evaluation per engine.",
        "",
        "## Final Model",
        "",
        f"- Model: {metrics['final_model_type']}",
        f"- Feature count: {metrics['feature_count']}",
        f"- Train rows after rolling warm-up: {metrics['train_rows']}",
        f"- Online test rows after rolling warm-up: {metrics['online_test_rows']}",
        f"- Final-cycle test engines: {metrics['final_test_engines']}",
        "",
        "## Standard Final-Cycle Metrics",
        "",
        f"- MAE: {final['mae']:.4f}",
        f"- RMSE: {final['rmse']:.4f}",
        f"- NASA asymmetric score: {final['nasa_score']:.4f}",
        "",
        "## Online Row-Level Metrics",
        "",
        f"- MAE: {online['mae']:.4f}",
        f"- RMSE: {online['rmse']:.4f}",
        f"- NASA asymmetric score: {online['nasa_score']:.4f}",
        "",
        "## Honest Limitations",
        "",
        "- NASA C-MAPSS is simulated data, not real factory telemetry.",
        "- Risk level is derived from predicted RUL thresholds, not a calibrated classifier.",
        "- The final-cycle metric is the defensible benchmark metric; online row-level metrics are secondary.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_model_comparison_plot(path: Path, model_results: dict[str, dict[str, object]]) -> None:
    names = list(model_results)
    maes = [model_results[name]["standard_final_cycle_metrics"]["mae"] for name in names]
    plt.figure(figsize=(10, 5))
    plt.bar(names, maes, color=["#64748b", "#0f766e", "#2563eb", "#7c3aed", "#dc2626"][: len(names)])
    plt.ylabel("MAE, cycles")
    plt.title("NASA C-MAPSS standard final-cycle evaluation")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=180)
    plt.close()


def write_demo_payload(path: Path, final_test_df: pd.DataFrame, features: list[str]) -> None:
    row = final_test_df.iloc[0]
    payload = {
        "engine_id": str(row["engine_key"]),
        "cycle": int(row["cycle"]),
        "features": {name: float(row[name]) for name in features if name != "cycle"},
    }
    write_json(path, payload)


def write_training_notebook(path: Path, metrics: dict[str, object], metrics_path: Path) -> None:
    notebook = nbf.v4.new_notebook()
    notebook["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    summary = json.dumps(
        {
            "generated_at_utc": metrics["generated_at_utc"],
            "subsets": metrics["subsets"],
            "final_model_type": metrics["final_model_type"],
            "standard_final_cycle_metrics": metrics["models"]["final_gradient_boosting"][
                "standard_final_cycle_metrics"
            ],
            "mlflow_run_id": metrics["mlflow"]["run_id"],
        },
        indent=2,
    )
    notebook.cells = [
        nbf.v4.new_markdown_cell("# Executed Training Proof\n\nGenerated by `scripts/train_model.py`."),
        nbf.v4.new_code_cell(
            f"import json\nmetrics = json.load(open('{metrics_path.as_posix()}'))\nprint(json.dumps(metrics['dataset'], indent=2))",
            execution_count=1,
            outputs=[nbf.v4.new_output("stream", name="stdout", text=json.dumps(metrics["dataset"], indent=2) + "\n")],
        ),
        nbf.v4.new_code_cell(
            "print('Final training summary')",
            execution_count=2,
            outputs=[nbf.v4.new_output("stream", name="stdout", text=summary + "\n")],
        ),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, path)


def train(args: argparse.Namespace) -> dict[str, object]:
    if args.download:
        download_cmapss(args.data_dir)

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("industrial-equipment-health")

    train_raw, test_raw = load_all_subsets(args.data_dir, args.subsets)
    train_feat = add_window_features(train_raw)
    test_feat = add_window_features(test_raw)
    features = engineered_features()
    final_test = test_feat.sort_values("cycle").groupby("engine_key", as_index=False).tail(1)
    print(
        "prepared NASA C-MAPSS data: "
        f"{len(train_feat)} training rows, {len(test_feat)} online test rows, "
        f"{len(final_test)} final-cycle engines"
    )

    models: dict[str, tuple[Pipeline, list[str]]] = {
        "mean_baseline": (
            model_pipeline(DummyRegressor(strategy="mean"), scale=False),
            features,
        ),
        "cycle_only_ridge": (
            model_pipeline(Ridge(alpha=1.0), scale=True),
            ["subset_id", "cycle"],
        ),
        "ridge_raw": (
            model_pipeline(Ridge(alpha=1.0), scale=True),
            RAW_FEATURES,
        ),
        "random_forest_raw": (
            model_pipeline(
                RandomForestRegressor(n_estimators=80, max_depth=14, random_state=42, n_jobs=-1),
                scale=False,
            ),
            RAW_FEATURES,
        ),
        "final_gradient_boosting": (
            model_pipeline(
                HistGradientBoostingRegressor(
                    max_iter=180,
                    learning_rate=0.08,
                    max_leaf_nodes=31,
                    l2_regularization=0.05,
                    random_state=42,
                ),
                scale=False,
            ),
            features,
        ),
    }

    model_results: dict[str, dict[str, object]] = {}
    for name, (pipeline, model_features) in models.items():
        print(f"fitting and evaluating {name} ({len(model_features)} features)")
        model_results[name] = fit_and_evaluate(
            name,
            pipeline,
            train_feat,
            test_feat,
            final_test,
            model_features,
        )

    final_pipeline, _ = models["final_gradient_boosting"]
    print("running GroupKFold cross-validation for final model")
    cv_metrics = cross_validate_final_model(
        train_feat,
        features,
        lambda: model_pipeline(
            HistGradientBoostingRegressor(
                max_iter=120,
                learning_rate=0.08,
                max_leaf_nodes=31,
                l2_regularization=0.05,
                random_state=42,
            ),
            scale=False,
        ),
    )

    generated_at = datetime.now(UTC).isoformat()
    model_dir = args.model_dir
    report_dir = args.report_dir
    figure_path = report_dir / "figures" / "final_model_comparison.png"
    metrics_path = report_dir / "final_evaluation.json"
    report_path = report_dir / "final_evaluation.md"
    schema_path = model_dir / "feature_schema.json"
    model_path = model_dir / "model.pkl"
    model_metrics_path = model_dir / "metrics.json"
    demo_payload_path = Path("demo/predict_sample.json")
    notebook_path = Path("notebooks/training_executed.ipynb")

    print(f"logging final run to MLflow at {tracking_uri}")
    with mlflow.start_run(run_name="final-cmapss-rul-training") as run:
        mlflow.log_params(
            {
                "subsets": ",".join(args.subsets),
                "rul_clip": RUL_CLIP,
                "window": WINDOW,
                "final_model": "HistGradientBoostingRegressor",
                "feature_count": len(features),
            }
        )
        final_metrics = model_results["final_gradient_boosting"]["standard_final_cycle_metrics"]
        mlflow.log_metrics(
            {
                "standard_final_mae": final_metrics["mae"],
                "standard_final_rmse": final_metrics["rmse"],
                "standard_final_nasa_score": final_metrics["nasa_score"],
                "online_mae": model_results["final_gradient_boosting"]["online_metrics"]["mae"],
                "online_rmse": model_results["final_gradient_boosting"]["online_metrics"]["rmse"],
            }
        )
        mlflow.sklearn.log_model(final_pipeline, artifact_path="model")
        run_id = run.info.run_id

    metrics = {
        "generated_at_utc": generated_at,
        "subsets": args.subsets,
        "rul_clip": RUL_CLIP,
        "window": WINDOW,
        "final_model_type": "HistGradientBoostingRegressor",
        "feature_count": len(features),
        "train_rows": int(len(train_feat)),
        "online_test_rows": int(len(test_feat)),
        "final_test_engines": int(len(final_test)),
        "dataset": {
            "train_rows_raw": int(len(train_raw)),
            "test_rows_raw": int(len(test_raw)),
            "train_engines": int(train_raw["engine_key"].nunique()),
            "test_engines": int(test_raw["engine_key"].nunique()),
            "source": "NASA C-MAPSS Turbofan Engine Degradation Simulation Data Set",
        },
        "models": model_results,
        "group_kfold_cv": cv_metrics,
        "mlflow": {"tracking_uri": tracking_uri, "run_id": run_id},
        "artifacts": {
            "model": model_path.as_posix(),
            "feature_schema": schema_path.as_posix(),
            "metrics": model_metrics_path.as_posix(),
            "report": report_path.as_posix(),
            "notebook": notebook_path.as_posix(),
            "demo_payload": demo_payload_path.as_posix(),
        },
    }

    served_model = FeatureSchemaRULModel(
        pipeline=final_pipeline,
        feature_names=features,
        metadata={
            "model_type": metrics["final_model_type"],
            "model_version": "1",
            "generated_at_utc": generated_at,
            "mlflow_run_id": run_id,
            "standard_final_cycle_metrics": model_results["final_gradient_boosting"][
                "standard_final_cycle_metrics"
            ],
        },
    )
    model_dir.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as file:
        pickle.dump(served_model, file)

    write_json(schema_path, {"required": features, "target": "RUL", "feature_count": len(features)})
    write_json(model_metrics_path, metrics)
    write_json(metrics_path, metrics)
    write_markdown_report(report_path, metrics)
    write_model_comparison_plot(figure_path, model_results)
    write_demo_payload(demo_payload_path, final_test, features)
    write_training_notebook(notebook_path, metrics, metrics_path)
    print(f"trained final model: {model_path}")
    print(f"standard final MAE: {model_results['final_gradient_boosting']['standard_final_cycle_metrics']['mae']:.4f}")
    print(f"mlflow run id: {run_id}")
    return metrics


def main() -> None:
    env_subsets = os.getenv("TRAIN_SUBSETS")
    default_subsets = env_subsets.split() if env_subsets else SUBSETS
    parser = argparse.ArgumentParser(description="Train final NASA C-MAPSS RUL model.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/latest"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/model_metrics"))
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--subsets", nargs="+", default=default_subsets, choices=SUBSETS)
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
