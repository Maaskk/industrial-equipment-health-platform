from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from industrial_health.mlops.drift import compute_numeric_drift


def read_rul_values(log_path: Path) -> list[float]:
    if not log_path.exists():
        return []
    values: list[float] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "remaining_useful_life" in row:
            values.append(float(row["remaining_useful_life"]))
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a simple monitoring drift report.")
    parser.add_argument("--log-path", type=Path, default=Path("logs/prediction_logs.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("reports/monitoring/drift_report.json"))
    parser.add_argument("--threshold", type=float, default=20.0)
    args = parser.parse_args()

    values = read_rul_values(args.log_path)
    if len(values) >= 4:
        midpoint = len(values) // 2
        baseline = values[:midpoint]
        current = values[midpoint:]
        source = args.log_path.as_posix()
    else:
        baseline = [120.0, 110.0, 100.0, 95.0]
        current = [76.0, 70.0, 65.0, 60.0]
        source = "demo_values_when_prediction_log_has_fewer_than_4_rows"

    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source": source,
        "metric": compute_numeric_drift(
            baseline=baseline,
            current=current,
            feature_name="remaining_useful_life",
            mean_shift_threshold=args.threshold,
        ).to_dict(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
