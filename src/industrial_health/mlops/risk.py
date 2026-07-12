from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskThresholds:
    high_max_rul: float = 30.0
    medium_max_rul: float = 80.0


def classify_risk(
    remaining_useful_life: float,
    thresholds: RiskThresholds = RiskThresholds(),
) -> str:
    """Classify equipment risk from predicted Remaining Useful Life."""

    rul = float(remaining_useful_life)
    if rul <= thresholds.high_max_rul:
        return "high"
    if rul <= thresholds.medium_max_rul:
        return "medium"
    return "low"

