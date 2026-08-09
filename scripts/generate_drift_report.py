from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from industrial_health.mlops.drift import evaluate_prediction_drift


def read_records(log_path: Path) -> list[dict[str, object]]:
    if not log_path.exists():
        return []
    records: list[dict[str, object]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "remaining_useful_life" in row:
            records.append(row)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a simple monitoring drift report.")
    parser.add_argument("--log-path", type=Path, default=Path("logs/prediction_logs.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("reports/monitoring/drift_report.json"))
    parser.add_argument("--threshold", type=float, default=20.0)
    args = parser.parse_args()

    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source": args.log_path.as_posix(),
        "drift": evaluate_prediction_drift(
            read_records(args.log_path),
            mean_shift_threshold=args.threshold,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
