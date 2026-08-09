from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from statistics import fmean, pstdev
from typing import Any


@dataclass(frozen=True)
class NumericDriftReport:
    feature_name: str
    baseline_mean: float
    current_mean: float
    absolute_mean_shift: float
    baseline_std: float
    current_std: float
    drift_detected: bool

    def to_dict(self) -> dict[str, bool | float | str]:
        return asdict(self)


def compute_numeric_drift(
    *,
    baseline: list[float],
    current: list[float],
    feature_name: str,
    mean_shift_threshold: float,
) -> NumericDriftReport:
    """Compute a small, explainable drift signal for the course demo."""

    if not baseline:
        raise ValueError("baseline must contain at least one value")
    if not current:
        raise ValueError("current must contain at least one value")

    baseline_values = [float(value) for value in baseline]
    current_values = [float(value) for value in current]
    baseline_mean = fmean(baseline_values)
    current_mean = fmean(current_values)
    absolute_mean_shift = abs(current_mean - baseline_mean)

    return NumericDriftReport(
        feature_name=feature_name,
        baseline_mean=round(baseline_mean, 6),
        current_mean=round(current_mean, 6),
        absolute_mean_shift=round(absolute_mean_shift, 6),
        baseline_std=round(pstdev(baseline_values), 6),
        current_std=round(pstdev(current_values), 6),
        drift_detected=absolute_mean_shift > mean_shift_threshold,
    )


def evaluate_prediction_drift(
    records: list[dict[str, Any]],
    *,
    min_observations: int = 8,
    min_unique_observations: int = 4,
    mean_shift_threshold: float = 10.0,
) -> dict[str, Any]:
    generated_at = datetime.now(UTC).isoformat()
    signatures = {
        (
            str(row.get("engine_id", "")),
            row.get("cycle"),
            round(float(row["remaining_useful_life"]), 6),
        )
        for row in records
        if "remaining_useful_life" in row
    }
    sample_count = len(records)
    unique_count = len(signatures)
    if sample_count < min_observations or unique_count < min_unique_observations:
        return {
            "status": "insufficient_data",
            "drift_detected": None,
            "generated_at_utc": generated_at,
            "sample_count": sample_count,
            "unique_observations": unique_count,
            "minimum_observations": min_observations,
            "minimum_unique_observations": min_unique_observations,
            "reason": "More varied production observations are required.",
        }

    midpoint = sample_count // 2
    report = compute_numeric_drift(
        baseline=[float(row["remaining_useful_life"]) for row in records[:midpoint]],
        current=[float(row["remaining_useful_life"]) for row in records[midpoint:]],
        feature_name="predicted_rul",
        mean_shift_threshold=mean_shift_threshold,
    )
    return {
        "status": "ready",
        "metric": "predicted_rul_mean_shift",
        "generated_at_utc": generated_at,
        "sample_count": sample_count,
        "unique_observations": unique_count,
        "baseline_count": midpoint,
        "current_count": sample_count - midpoint,
        "mean_shift_threshold": mean_shift_threshold,
        **report.to_dict(),
    }
