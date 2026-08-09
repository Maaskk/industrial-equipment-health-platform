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
import duckdb
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException
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


def promotion_decision(
    champion_metrics: dict[str, float] | None,
    candidate_metrics: dict[str, float],
) -> dict[str, bool | str]:
    if champion_metrics is None:
        return {"promote": True, "reason": "no_existing_champion"}
    promote = (
        float(candidate_metrics["mae"]) <= float(champion_metrics["mae"])
        and float(candidate_metrics["rmse"]) <= float(champion_metrics["rmse"])
    )
    return {
        "promote": promote,
        "reason": (
            "candidate_improved_mae_and_rmse"
            if promote
            else "candidate_did_not_improve_mae_and_rmse"
        ),
    }


def current_champion(
    client: MlflowClient, model_name: str, alias: str
) -> tuple[dict[str, float] | None, str | None, str | None]:
    try:
        version = client.get_model_version_by_alias(model_name, alias)
        run = client.get_run(version.run_id)
    except MlflowException:
        return None, None, None
    metrics = run.data.metrics
    if "standard_final_mae" not in metrics or "standard_final_rmse" not in metrics:
        return None, str(version.version), version.run_id
    return (
        {
            "mae": float(metrics["standard_final_mae"]),
            "rmse": float(metrics["standard_final_rmse"]),
        },
        str(version.version),
        version.run_id,
    )


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


def load_from_duckdb(db_path: Path, subsets: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the dbt-curated mart and staged labels used by the final ML pipeline."""

    if not db_path.exists():
        raise FileNotFoundError(
            f"DuckDB warehouse not found at {db_path}. Run `python orchestration/run_local.py` first."
        )
    subset_ids = [SUBSETS.index(subset) + 1 for subset in subsets]
    placeholders = ", ".join("?" for _ in subset_ids)
    with duckdb.connect(str(db_path), read_only=True) as connection:
        mart = connection.execute(
            f"""SELECT * FROM marts.fct_equipment_health_features
                WHERE subset_id IN ({placeholders})""",
            subset_ids,
        ).fetchdf()
        labels = connection.execute("SELECT engine_id, rul FROM staging.stg_rul_labels").fetchdf()

    rename = {f"setting_{index}": f"op_setting_{index}" for index in range(1, 4)}
    mart = mart.rename(columns=rename)
    mart["subset"] = mart["source_file"].str.extract(r"(FD\d{3})", expand=False)
    mart["unit"] = mart["engine_id"].str.rsplit("_", n=1).str[-1].astype(int)
    mart["engine_key"] = mart["subset"] + "_" + mart["unit"].astype(str)

    train = mart[mart["split"] == "train"].copy()
    train["RUL"] = train.groupby("engine_key")["cycle"].transform("max") - train["cycle"]

    test = mart[mart["split"] == "test"].copy()
    label_map = labels.set_index("engine_id")["rul"]
    last_cycle = test.groupby("engine_key")["cycle"].max()
    final_rul = test["engine_id"].map(label_map)
    if final_rul.isna().any():
        missing = sorted(test.loc[final_rul.isna(), "engine_id"].unique())[:8]
        raise RuntimeError(f"Missing staged test RUL labels for engines: {missing}")
    test["RUL"] = test["engine_key"].map(last_cycle) + final_rul - test["cycle"]
    for frame in (train, test):
        frame["RUL"] = frame["RUL"].clip(upper=RUL_CLIP)
    return train.reset_index(drop=True), test.reset_index(drop=True)


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


def build_release_manifest(
    *,
    generated_at: str,
    git_sha: str,
    git_tag: str,
    git_branch: str,
    model_name: str,
    model_alias: str,
    model_version: str,
    run_id: str,
    subsets: list[str],
    final_metrics: dict[str, float],
    promotion: dict[str, bool | str],
) -> dict[str, object]:
    return {
        "git_sha": git_sha,
        "git_tag": git_tag,
        "branch": git_branch,
        "deployment_time": generated_at,
        "model_name": model_name,
        "model_version": model_version,
        "mlflow_run_id": run_id,
        "model_alias": model_alias,
        "training_subsets": subsets,
        "mae": float(final_metrics["mae"]),
        "rmse": float(final_metrics["rmse"]),
        "nasa_score": float(final_metrics["nasa_score"]),
        "candidate_promoted": bool(promotion["promote"]),
        "promotion_reason": str(promotion["reason"]),
    }


def write_release_manifest(
    release_dir: Path, manifest: dict[str, object]
) -> tuple[Path, Path]:
    json_path = release_dir / "final_release.json"
    markdown_path = release_dir / "final_release.md"
    write_json(json_path, manifest)

    lines = [
        "# Production Release",
        "",
        f"Deployment time (UTC): {manifest['deployment_time']}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Git branch | {manifest['branch']} |",
        f"| Git tag | {manifest['git_tag']} |",
        f"| Git SHA | {manifest['git_sha']} |",
        f"| Model | {manifest['model_name']} |",
        f"| Model alias | {manifest['model_alias']} |",
        f"| Model version | {manifest['model_version']} |",
        f"| MLflow run | {manifest['mlflow_run_id']} |",
        f"| Training subsets | {', '.join(manifest['training_subsets'])} |",
        f"| Final cycle MAE | {float(manifest['mae']):.4f} |",
        f"| Final cycle RMSE | {float(manifest['rmse']):.4f} |",
        f"| Candidate promoted | {str(manifest['candidate_promoted']).lower()} |",
        "",
    ]
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, markdown_path


def write_markdown_report(path: Path, metrics: dict[str, object]) -> None:
    final = metrics["models"]["final_gradient_boosting"]["standard_final_cycle_metrics"]
    online = metrics["models"]["final_gradient_boosting"]["online_metrics"]
    lines = [
        "# Final Model Evaluation",
        "",
        "The final model trains on NASA C-MAPSS FD001-FD004 when all files are present.",
        "The primary score is the standard final-observed-cycle test evaluation per engine.",
        "",
        "## Selected Estimator",
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


def train(args: argparse.Namespace) -> dict[str, object]:
    if args.download:
        download_cmapss(args.data_dir)

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("industrial-equipment-health")

    if args.source == "duckdb":
        train_raw, test_raw = load_from_duckdb(args.duckdb_path, args.subsets)
    else:
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

    model_name = os.getenv("MODEL_NAME", "industrial-equipment-health-model")
    model_alias = os.getenv("MODEL_ALIAS", "champion")
    registry_client = MlflowClient()
    champion_metrics, champion_version, champion_run_id = current_champion(
        registry_client, model_name, model_alias
    )
    final_metrics = model_results["final_gradient_boosting"]["standard_final_cycle_metrics"]
    promotion = promotion_decision(champion_metrics, final_metrics)

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
        mlflow.log_metrics(
            {
                "standard_final_mae": final_metrics["mae"],
                "standard_final_rmse": final_metrics["rmse"],
                "standard_final_nasa_score": final_metrics["nasa_score"],
                "online_mae": model_results["final_gradient_boosting"]["online_metrics"]["mae"],
                "online_rmse": model_results["final_gradient_boosting"]["online_metrics"]["rmse"],
            }
        )
        mlflow.log_dict(
            {
                "generated_at_utc": generated_at,
                "model_type": "HistGradientBoostingRegressor",
                "training_subsets": args.subsets,
                "standard_final_cycle_metrics": final_metrics,
                "promotion": promotion,
                "previous_champion_version": champion_version,
                "previous_champion_run_id": champion_run_id,
            },
            "release_evaluation.json",
        )
        mlflow.set_tags(
            {
                "model_alias_candidate": model_alias,
                "promotion_decision": str(promotion["promote"]).lower(),
                "promotion_reason": str(promotion["reason"]),
            }
        )
        model_info = mlflow.sklearn.log_model(
            final_pipeline,
            artifact_path="model",
            registered_model_name=model_name,
            serialization_format="cloudpickle",
            input_example=train_feat[features].head(2),
        )
        run_id = run.info.run_id

    registered_version = str(model_info.registered_model_version)
    if promotion["promote"]:
        registry_client.set_registered_model_alias(model_name, model_alias, registered_version)

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
            "pipeline_source": args.source,
            "duckdb_path": args.duckdb_path.as_posix() if args.source == "duckdb" else None,
        },
        "models": model_results,
        "group_kfold_cv": cv_metrics,
        "mlflow": {
            "tracking_uri": tracking_uri,
            "run_id": run_id,
            "registered_model_name": model_name,
            "registered_model_version": registered_version,
            "registered_model_alias": model_alias,
            "model_uri": f"models:/{model_name}@{model_alias}",
        },
        "promotion": {
            **promotion,
            "candidate_version": registered_version,
            "previous_champion_version": champion_version,
            "previous_champion_run_id": champion_run_id,
            "criteria": "candidate MAE and RMSE must both be no worse than champion",
        },
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
            "model_version": registered_version,
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
    release_manifest = build_release_manifest(
        generated_at=generated_at,
        git_sha=os.getenv("RELEASE_SHA", "unrecorded"),
        git_tag=os.getenv("RELEASE_TAG", "unreleased"),
        git_branch=os.getenv("RELEASE_BRANCH", "production"),
        model_name=model_name,
        model_alias=model_alias,
        model_version=registered_version,
        run_id=run_id,
        subsets=args.subsets,
        final_metrics=final_metrics,
        promotion=promotion,
    )
    write_release_manifest(Path("reports/release"), release_manifest)
    print(f"trained final model: {model_path}")
    print(f"standard final MAE: {model_results['final_gradient_boosting']['standard_final_cycle_metrics']['mae']:.4f}")
    print(f"mlflow run id: {run_id}")
    print(f"registered model: {model_name} version {registered_version}")
    print(f"champion promotion: {promotion['promote']} ({promotion['reason']})")
    return metrics


def main() -> None:
    env_subsets = os.getenv("TRAIN_SUBSETS")
    default_subsets = env_subsets.split() if env_subsets else SUBSETS
    parser = argparse.ArgumentParser(description="Train final NASA C-MAPSS RUL model.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/latest"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/model_metrics"))
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--source", choices=["duckdb", "raw"], default=os.getenv("TRAIN_SOURCE", "duckdb"))
    parser.add_argument("--duckdb-path", type=Path, default=Path(os.getenv("DUCKDB_PATH", "cmapss_ingestion.duckdb")))
    parser.add_argument("--subsets", nargs="+", default=default_subsets, choices=SUBSETS)
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
