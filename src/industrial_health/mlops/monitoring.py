from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


class PredictionMonitor:
    """Append prediction telemetry as JSONL for a simple local monitoring demo."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path

    def record_prediction(
        self,
        *,
        engine_id: str,
        remaining_useful_life: float,
        risk_level: str,
        model_version: str,
        latency_ms: float,
    ) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "engine_id": engine_id,
            "remaining_useful_life": float(remaining_useful_life),
            "risk_level": risk_level,
            "model_version": model_version,
            "latency_ms": float(latency_ms),
        }
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(row, sort_keys=True) + "\n")

