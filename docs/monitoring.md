# Monitoring

## Signals

| Signal | Evidence |
|---|---|
| API readiness | `GET /health` |
| Release identity | `release_sha` and `release_tag` in `/health` |
| Registry identity | model name, resolved version, source, and URI in `/health` |
| Prediction result | RUL, risk, model version, and latency |
| Request trace | `X-Request-ID` response header |
| Prediction history | persistent `logs/prediction_logs.jsonl` |
| Distribution change | `/api/monitoring/summary` and drift report |

## Drift rule

The current signal compares mean predicted RUL between the first and second halves of the observation window. It requires at least eight records and four distinct engine/cycle/prediction signatures.

When those conditions are not met, the API returns:

```json
{
  "status": "insufficient_data",
  "drift_detected": null
}
```

Repeated identical predictions cannot produce a `no drift` result. The ready report records the sample count, unique count, split sizes, metric, threshold, result, and UTC timestamp.

Generate the stored report with:

```bash
python scripts/generate_drift_report.py
```

This is a predicted-RUL mean-shift indicator. It is not feature drift, concept drift, or a statistical production alerting system.
