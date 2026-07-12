from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class ReadinessItem:
    name: str
    ready: bool
    evidence: str


def build_readiness_report(
    *,
    output_path: Path,
    items: list[ReadinessItem],
) -> dict[str, object]:
    ready_count = sum(1 for item in items if item.ready)
    status = "ready" if ready_count == len(items) else "partial"
    report: dict[str, object] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "ready_count": ready_count,
        "total_count": len(items),
        "items": [asdict(item) for item in items],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report

