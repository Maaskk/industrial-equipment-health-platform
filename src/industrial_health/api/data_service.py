from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from threading import Lock
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from industrial_health.api.contracts import build_prediction_response
from industrial_health.mlops.drift import evaluate_prediction_drift
from industrial_health.mlops.monitoring import PredictionMonitor


SENSORS = [f"sensor_{index}" for index in range(1, 22)]
SETTINGS = [f"setting_{index}" for index in range(1, 4)]
RAW_COLUMNS = ["cycle", *SETTINGS, *SENSORS]
RUL_CLIP = 125.0


class DatasetUnavailableError(RuntimeError):
    pass


class EngineNotFoundError(LookupError):
    pass


class CycleNotFoundError(LookupError):
    pass


class InsufficientHistoryError(ValueError):
    pass


def public_engine_id(database_id: str) -> str:
    value = database_id.removeprefix("test_").removeprefix("train_")
    subset, unit = value.rsplit("_", 1)
    return f"{subset}_{int(unit):03d}"


def database_engine_id(engine_id: str, split: str = "test") -> str:
    clean = engine_id.strip().upper()
    if clean.startswith(("TEST_", "TRAIN_")):
        return clean.lower().replace("fd", "FD", 1)
    try:
        subset, unit = clean.rsplit("_", 1)
        if subset not in {"FD001", "FD002", "FD003", "FD004"}:
            raise ValueError
        return f"{split}_{subset}_{int(unit)}"
    except ValueError as exc:
        raise EngineNotFoundError(f"Invalid engine ID: {engine_id}") from exc


def recommendation(risk: str) -> str:
    return {
        "low": "Continue operation and monitor",
        "medium": "Schedule inspection",
        "high": "Remove from service",
    }[risk]


def feature_row(frame: pd.DataFrame, subset_id: int) -> dict[str, float]:
    ordered = frame.sort_values("cycle").tail(5)
    if len(ordered) < 5:
        raise InsufficientHistoryError("At least five consecutive cycles are required")
    expected = set(RAW_COLUMNS)
    missing = sorted(expected - set(ordered.columns))
    if missing:
        raise ValueError(f"Missing raw columns: {missing}")
    if ordered["cycle"].diff().dropna().ne(1).any():
        raise InsufficientHistoryError("The five latest cycles must be consecutive")

    latest = ordered.iloc[-1]
    sensor_matrix = ordered[SENSORS].to_numpy(dtype=float)
    sensor_means = sensor_matrix.mean(axis=0)
    sensor_stds = sensor_matrix.std(axis=0, ddof=1)
    x = np.arange(len(sensor_matrix), dtype=float)
    centered_x = x - x.mean()
    slopes = (
        centered_x[:, None] * (sensor_matrix - sensor_means[None, :])
    ).sum(axis=0) / float((centered_x**2).sum())
    row: dict[str, float] = {
        "subset_id": float(subset_id),
        "cycle": float(latest["cycle"]),
    }
    for index in range(1, 4):
        row[f"op_setting_{index}"] = float(latest[f"setting_{index}"])
    for index, sensor in enumerate(SENSORS):
        row[sensor] = float(sensor_matrix[-1, index])
        row[f"{sensor}_roll_mean"] = float(sensor_means[index])
        row[f"{sensor}_roll_std"] = float(sensor_stds[index])
        row[f"{sensor}_roll_slope"] = float(slopes[index])
    return row


@dataclass
class EngineDataService:
    db_path: Path
    model: Any
    model_version: str
    monitor: PredictionMonitor
    metrics_path: Path
    drift_path: Path

    def __post_init__(self) -> None:
        self._fleet_cache: list[dict[str, Any]] | None = None
        self._cache_lock = Lock()

    def _connect(self) -> duckdb.DuckDBPyConnection:
        if not self.db_path.exists():
            raise DatasetUnavailableError(f"DuckDB warehouse is unavailable: {self.db_path}")
        return duckdb.connect(str(self.db_path), read_only=True)

    def _engine_metadata(self, engine_id: str) -> tuple[str, int, int]:
        internal = database_engine_id(engine_id)
        with self._connect() as connection:
            result = connection.execute(
                """SELECT subset_id, max(cycle)
                   FROM marts.fct_equipment_health_features
                   WHERE engine_id = ? AND split = 'test'
                   GROUP BY subset_id""",
                [internal],
            ).fetchone()
        if result is None:
            raise EngineNotFoundError(f"Unknown C-MAPSS engine: {engine_id}")
        return internal, int(result[0]), int(result[1])

    def engines(self, subset: str | None = None) -> list[dict[str, Any]]:
        where = "WHERE split = 'test'"
        params: list[Any] = []
        if subset:
            subset_id = int(subset.upper().removeprefix("FD"))
            where += " AND subset_id = ?"
            params.append(subset_id)
        with self._connect() as connection:
            rows = connection.execute(
                f"""SELECT engine_id, subset_id, max(cycle) AS latest_cycle
                    FROM marts.fct_equipment_health_features
                    {where}
                    GROUP BY engine_id, subset_id
                    ORDER BY subset_id, engine_id""",
                params,
            ).fetchall()
        return [
            {
                "engine_id": public_engine_id(row[0]),
                "subset": f"FD{int(row[1]):03d}",
                "latest_cycle": int(row[2]),
            }
            for row in rows
        ]

    def cycle_history(self, engine_id: str, cycle: int | None = None) -> pd.DataFrame:
        internal, _, latest_cycle = self._engine_metadata(engine_id)
        selected = latest_cycle if cycle is None else cycle
        with self._connect() as connection:
            frame = connection.execute(
                f"""SELECT {', '.join(RAW_COLUMNS)}
                    FROM marts.fct_equipment_health_features
                    WHERE engine_id = ? AND split = 'test' AND cycle <= ?
                    ORDER BY cycle""",
                [internal, selected],
            ).fetchdf()
        if frame.empty or int(frame.iloc[-1]["cycle"]) != selected:
            raise CycleNotFoundError(f"Cycle {selected} is unavailable for {engine_id}")
        return frame

    def cycles(self, engine_id: str) -> dict[str, Any]:
        _, _, latest = self._engine_metadata(engine_id)
        return {"engine_id": engine_id, "cycles": list(range(1, latest + 1)), "latest_cycle": latest}

    def sensor_series(
        self,
        engine_id: str,
        cycle: int,
        sensors: list[str],
        normalized: bool = False,
    ) -> dict[str, Any]:
        selected = [sensor for sensor in sensors if sensor in SENSORS][:3] or [
            "sensor_2",
            "sensor_3",
            "sensor_11",
        ]
        frame = self.cycle_history(engine_id, cycle)
        series: dict[str, list[float]] = {}
        for sensor in selected:
            values = frame[sensor].astype(float)
            if normalized:
                std = float(values.std(ddof=0))
                values = (values - values.mean()) / (std or 1.0)
            series[sensor] = [round(float(value), 6) for value in values]
        return {
            "engine_id": engine_id,
            "cycle": cycle,
            "cycles": frame["cycle"].astype(int).tolist(),
            "series": series,
            "normalized": normalized,
        }

    def actual_rul(self, engine_id: str, cycle: int) -> float:
        internal, _, latest = self._engine_metadata(engine_id)
        with self._connect() as connection:
            label = connection.execute(
                "SELECT rul FROM staging.stg_rul_labels WHERE engine_id = ?", [internal]
            ).fetchone()
        if label is None:
            raise DatasetUnavailableError(f"Missing test label for {engine_id}")
        return round(min(RUL_CLIP, latest + float(label[0]) - cycle), 2)

    def predict_cycle(
        self,
        engine_id: str,
        cycle: int,
        *,
        include_truth: bool = False,
        record: bool = True,
    ) -> dict[str, Any]:
        _, subset_id, _ = self._engine_metadata(engine_id)
        frame = self.cycle_history(engine_id, cycle)
        features = feature_row(frame, subset_id)
        started = datetime.now(UTC)
        rul = self.model.predict_one(features)
        latency_ms = (datetime.now(UTC) - started).total_seconds() * 1000
        response: dict[str, Any] = build_prediction_response(
            engine_id=engine_id,
            remaining_useful_life=rul,
            model_version=self.model_version,
            latency_ms=latency_ms,
        )
        response.update(
            {
                "cycle": cycle,
                "subset": engine_id.split("_")[0],
                "recommendation": recommendation(str(response["risk_level"])),
                "sensor_profile": {
                    sensor: round(float(frame.iloc[-1][sensor]), 6) for sensor in SENSORS
                },
            }
        )
        if include_truth:
            actual = self.actual_rul(engine_id, cycle)
            response["actual_rul"] = actual
            response["prediction_error"] = round(float(response["remaining_useful_life"]) - actual, 2)
        if record:
            self.monitor.record_prediction(
                engine_id=engine_id,
                remaining_useful_life=float(response["remaining_useful_life"]),
                risk_level=str(response["risk_level"]),
                model_version=self.model_version,
                latency_ms=float(response["latency_ms"]),
                cycle=cycle,
                subset=str(response["subset"]),
            )
        return response

    def engine_detail(
        self, engine_id: str, cycle: int | None = None, evaluation: bool = False
    ) -> dict[str, Any]:
        _, _, latest = self._engine_metadata(engine_id)
        selected = latest if cycle is None else cycle
        prediction = self.predict_cycle(
            engine_id, selected, include_truth=evaluation, record=False
        )
        profile = self.cycle_history(engine_id, selected).iloc[-1]
        prediction["latest_cycle"] = latest
        prediction["sensor_profile"] = {
            sensor: round(float(profile[sensor]), 6) for sensor in SENSORS
        }
        return prediction

    def _build_fleet(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            frame = connection.execute(
                f"""SELECT engine_id, subset_id, {', '.join(RAW_COLUMNS)}
                    FROM (
                        SELECT engine_id, subset_id, {', '.join(RAW_COLUMNS)},
                               row_number() OVER (
                                   PARTITION BY engine_id ORDER BY cycle DESC
                               ) AS recent_rank
                        FROM marts.fct_equipment_health_features
                        WHERE split = 'test'
                    )
                    WHERE recent_rank <= 5
                    ORDER BY engine_id, cycle"""
            ).fetchdf()
        prepared: list[tuple[str, int, int, dict[str, float]]] = []
        engine_values = frame["engine_id"].astype(str).to_numpy()
        boundaries = np.flatnonzero(engine_values[1:] != engine_values[:-1]) + 1
        starts = np.r_[0, boundaries]
        ends = np.r_[boundaries, len(frame)]
        raw_values = frame[RAW_COLUMNS].to_numpy(dtype=float)
        subset_values = frame["subset_id"].to_numpy(dtype=int)
        for start, end in zip(starts, ends, strict=True):
            try:
                values = raw_values[start:end]
                if len(values) < 5 or np.any(np.diff(values[:, 0]) != 1):
                    raise InsufficientHistoryError
                subset_id = int(subset_values[end - 1])
                sensors = values[:, 4:]
                means = sensors.mean(axis=0)
                stds = sensors.std(axis=0, ddof=1)
                centered_x = np.arange(len(values), dtype=float) - (len(values) - 1) / 2
                slopes = (centered_x[:, None] * (sensors - means)).sum(axis=0) / float(
                    (centered_x**2).sum()
                )
                features = {
                    "subset_id": float(subset_id),
                    "cycle": float(values[-1, 0]),
                    **{f"op_setting_{index}": float(values[-1, index]) for index in range(1, 4)},
                }
                for index, sensor in enumerate(SENSORS):
                    features[sensor] = float(sensors[-1, index])
                    features[f"{sensor}_roll_mean"] = float(means[index])
                    features[f"{sensor}_roll_std"] = float(stds[index])
                    features[f"{sensor}_roll_slope"] = float(slopes[index])
                public_id = public_engine_id(engine_values[end - 1])
            except (InsufficientHistoryError, ValueError, IndexError):
                continue
            prepared.append((public_id, subset_id, int(values[-1, 0]), features))

        feature_names = list(getattr(self.model, "feature_names", []))
        predictor = getattr(self.model, "pipeline", None) or getattr(self.model, "model", None)
        if predictor is not None and feature_names:
            matrix = np.asarray(
                [[features[name] for name in feature_names] for *_, features in prepared],
                dtype=float,
            )
            predictions = [max(0.0, float(value)) for value in predictor.predict(matrix)]
        else:
            predictions = [self.model.predict_one(features) for *_, features in prepared]

        rows: list[dict[str, Any]] = []
        for (public_id, subset_id, latest_cycle, _), rul in zip(
            prepared, predictions, strict=True
        ):
            prediction = build_prediction_response(
                engine_id=public_id,
                remaining_useful_life=rul,
                model_version=self.model_version,
                latency_ms=0.0,
            )
            risk = str(prediction["risk_level"])
            rows.append(
                {
                    "engine_id": public_id,
                    "subset": f"FD{subset_id:03d}",
                    "latest_cycle": latest_cycle,
                    **prediction,
                    "recommendation": recommendation(risk),
                }
            )
        return rows

    def fleet(self) -> list[dict[str, Any]]:
        if self._fleet_cache is None:
            with self._cache_lock:
                if self._fleet_cache is None:
                    self._fleet_cache = self._build_fleet()
        return list(self._fleet_cache)

    def fleet_summary(self) -> dict[str, Any]:
        rows = self.fleet()
        risks = {"low": 0, "medium": 0, "high": 0}
        for row in rows:
            risks[str(row["risk_level"])] += 1
        return {
            "total_engines": len(rows),
            "risk_counts": risks,
            "median_predicted_rul": round(
                median(float(row["remaining_useful_life"]) for row in rows), 2
            )
            if rows
            else None,
            "champion_version": self.model_version,
            "pipeline_health": "healthy" if rows else "unavailable",
        }

    def score_csv(self, csv_text: str) -> tuple[list[dict[str, Any]], str]:
        try:
            frame = pd.read_csv(io.StringIO(csv_text))
        except Exception as exc:
            raise ValueError("The uploaded CSV could not be parsed") from exc
        required = {"engine_id", *RAW_COLUMNS}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"Missing CSV columns: {missing}")
        results: list[dict[str, Any]] = []
        for engine_id, group in frame.groupby("engine_id", sort=True):
            public_id = str(engine_id).upper()
            subset = public_id.split("_")[0]
            if subset not in {"FD001", "FD002", "FD003", "FD004"}:
                raise ValueError(f"Cannot infer subset from engine ID: {engine_id}")
            features = feature_row(group, int(subset.removeprefix("FD")))
            rul = self.model.predict_one(features)
            response = build_prediction_response(
                engine_id=public_id,
                remaining_useful_life=rul,
                model_version=self.model_version,
                latency_ms=0.0,
            )
            response.update(
                {
                    "last_cycle": int(group["cycle"].max()),
                    "recommendation": recommendation(str(response["risk_level"])),
                }
            )
            results.append(response)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(results[0]) if results else [])
        if results:
            writer.writeheader()
            writer.writerows(results)
        return results, output.getvalue()

    def monitoring_summary(self) -> dict[str, Any]:
        path = self.monitor.log_path
        if not path.exists():
            return {
                "total_predictions": 0,
                "median_latency_ms": None,
                "p95_latency_ms": None,
                "risk_counts": {"low": 0, "medium": 0, "high": 0},
                "drift": evaluate_prediction_drift([]),
                "recent": [],
            }
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        latencies = [float(row["latency_ms"]) for row in records]
        risks = {"low": 0, "medium": 0, "high": 0}
        for row in records:
            risk = str(row.get("risk_level", ""))
            if risk in risks:
                risks[risk] += 1
        previous_by_engine: dict[str, float] = {}
        for row in records:
            engine_id = str(row.get("engine_id", ""))
            current_rul = float(row["remaining_useful_life"])
            previous = previous_by_engine.get(engine_id)
            row["change_from_previous"] = (
                round(current_rul - previous, 2) if previous is not None else None
            )
            previous_by_engine[engine_id] = current_rul
        drift = evaluate_prediction_drift(records)
        return {
            "total_predictions": len(records),
            "successful_predictions": len(records),
            "median_latency_ms": round(median(latencies), 2) if latencies else None,
            "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2)
            if latencies
            else None,
            "risk_counts": risks,
            "drift": drift,
            "recent": records[-20:][::-1],
        }

    def model_info(self) -> dict[str, Any]:
        if not self.metrics_path.exists():
            return {"status": "No observations available"}
        metrics = json.loads(self.metrics_path.read_text(encoding="utf-8"))
        final = metrics["models"]["final_gradient_boosting"]["standard_final_cycle_metrics"]
        return {
            "name": metrics["mlflow"]["registered_model_name"],
            "alias": metrics["mlflow"]["registered_model_alias"],
            "version": self.model_version,
            "model_type": metrics["final_model_type"],
            "datasets": ["FD001", "FD002", "FD003", "FD004"],
            "feature_count": metrics["feature_count"],
            "training_date": metrics["generated_at_utc"],
            "mae": round(float(final["mae"]), 4),
            "rmse": round(float(final["rmse"]), 4),
            "nasa_score": round(float(final["nasa_score"]), 2),
        }

    def platform_status(self) -> dict[str, Any]:
        with self._connect() as connection:
            raw_rows = int(
                connection.execute("SELECT count(*) FROM raw.raw_sensor_readings").fetchone()[0]
            )
            dbt_rows = int(
                connection.execute(
                    "SELECT count(*) FROM marts.fct_equipment_health_features"
                ).fetchone()[0]
            )
        return {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "pipeline": [
                {"name": "dlt ingestion", "status": "ready", "evidence": f"{raw_rows:,} rows"},
                {"name": "DuckDB", "status": "ready", "evidence": self.db_path.name},
                {"name": "dbt feature mart", "status": "ready", "evidence": f"{dbt_rows:,} rows"},
                {"name": "data contracts", "status": "ready", "evidence": "11 dbt tests"},
                {"name": "MLflow Registry", "status": "ready", "evidence": f"champion v{self.model_version}"},
                {"name": "FastAPI", "status": "ready", "evidence": "prediction service loaded"},
            ],
            "model": self.model_info(),
            "monitoring": self.monitoring_summary(),
        }
