# Demo Checklist

## Browser tabs

1. GitHub release and passing CI run.
2. Komodo Server `vh3`, then Stack `industrial_equipment_health_platform`.
3. University dashboard: `http://exp.s3.fsbm.ma:3402/`.
4. MLflow: `http://exp.s3.fsbm.ma:3401/` when access is available.
5. Dagster: `http://exp.s3.fsbm.ma:3403/` when access is available.

## Live sequence

1. Confirm `vh3` is `Ok` and the Stack is running.
2. Show `api`, `mlflow`, `dagster-webserver`, and `dagster-daemon` running; `training-init` exited successfully.
3. Open Fleet Overview and filter the C-MAPSS engines.
4. Use Engine Replay, cycle controls, sensor history, component focus, and exploded view.
5. Compare Operations mode with Evaluation mode.
6. Run a valid Prediction Lab request and an invalid request.
7. Score a CSV batch and create a maintenance recommendation.
8. Open Platform and explain model, pipeline, latency, logs, and drift status.
9. Show the MLflow run, registered model version, `champion` alias, metrics, and release evaluation artifact.
10. Show the Dagster asset graph, schedule state, daemon status, and a successful run.

## External verification

```bash
python scripts/verify_release.py \
  --base-url http://exp.s3.fsbm.ma:3402 \
  --expected-sha <release-sha>
```

Say “C-MAPSS degradation replay.” Do not call it live aircraft telemetry. Describe the Three.js view as an explanatory sensor map, not a physical simulation. If drift evidence is insufficient, say exactly that; do not call it “no drift.”
