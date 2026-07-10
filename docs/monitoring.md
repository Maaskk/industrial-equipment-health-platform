# Monitoring and Observability

Owner: `Maaskk`

This project uses a simple monitoring layer that is easy to explain during the demo and easy to replace later with Prometheus, Grafana, or Evidently.

## What We Monitor

| Signal | Why it matters | Current implementation |
|---|---|---|
| Service availability | Proves the API is alive and loaded a real model | `GET /health` returns `status`, `model_loaded`, `model_source`, feature counts, MLflow URI |
| Response latency | Shows serving performance | `latency_ms` in each prediction response |
| Prediction logs | Creates traceability | `logs/prediction_logs.jsonl` |
| Model version | Shows registry discipline | `model_version` in health and prediction responses |
| Simple drift | Detects prediction distribution shift | `scripts/generate_drift_report.py` using `industrial_health.mlops.drift` |

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

Generate a drift report:

```bash
PYTHONPATH=src python scripts/generate_drift_report.py
```

Output is saved to:

```text
reports/monitoring/drift_report.json
```

If the prediction log has at least four rows, the script compares the first half against the second half. If the log is still empty during a rehearsal, it writes a transparent demo report using documented sample values. This is intentionally simple enough to explain during the course demo and can later be upgraded to Evidently, Prometheus, or Grafana.

## Operational Expectations

- `/health` must return `model_source: local_pickle` for the real demo.
- `ALLOW_FALLBACK_MODEL=true` is only allowed in unit tests.
- Each `/predict` call must append one JSONL line.
- A failed model load should stop the API instead of serving fake predictions.
- The final release should include `reports/model_metrics/final_evaluation.json`, `notebooks/training_executed.ipynb`, and at least one `reports/monitoring/drift_report.json` generated during rehearsal.
