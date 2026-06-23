# Monitoring and Observability

Owner: `Maaskk`

This project uses a simple monitoring layer that is easy to explain during the demo and easy to replace later with Prometheus, Grafana, or Evidently.

## What We Monitor

| Signal | Why it matters | Current implementation |
|---|---|---|
| Service availability | Proves the API is alive | `GET /health` |
| Response latency | Shows serving performance | `latency_ms` in each prediction response |
| Prediction logs | Creates traceability | `logs/prediction_logs.jsonl` |
| Model version | Shows registry discipline | `model_version` in health and prediction responses |
| Simple drift | Detects sensor distribution change | `compute_numeric_drift` in `industrial_health.mlops.drift` |

## Prediction Log Format

Each prediction appends one JSON line:

```json
{
  "timestamp_utc": "2026-06-23T10:00:00+00:00",
  "engine_id": "engine_001",
  "remaining_useful_life": 24.25,
  "risk_level": "high",
  "model_version": "1",
  "latency_ms": 8.4
}
```

## Drift Demo

The first drift check compares a baseline sensor distribution against a current batch:

```python
from industrial_health.mlops.drift import compute_numeric_drift

report = compute_numeric_drift(
    baseline=[10.0, 11.0, 12.0, 13.0],
    current=[40.0, 41.0, 42.0, 43.0],
    feature_name="sensor_7",
    mean_shift_threshold=5.0,
)

print(report.to_dict())
```

This is intentionally transparent: the professor can understand the calculation and the team can later upgrade it.

