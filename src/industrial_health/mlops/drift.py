from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import fmean, pstdev


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

