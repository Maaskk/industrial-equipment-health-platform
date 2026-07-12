# Final Demo Checklist

Owner: `Maaskk`

## Before the Demo

- `main` has the final merged code.
- Docker builds successfully.
- MLflow opens locally.
- API health endpoint returns `status: ready` and identifies the loaded model source.
- Prediction endpoint returns RUL, risk level, model version, and latency.
- Prediction logs are generated.
- At least one drift example is ready.

## Demo Flow

1. Show repository structure and team branches.
2. Show data source and NASA dataset citation.
3. Run or explain the DataOps pipeline.
4. Show MLflow experiments and registered model.
5. Start the full stack with one Docker Compose command.
6. Open Fleet Overview and identify it as a C-MAPSS dataset replay, not live telemetry.
7. Filter the fleet and open an engine in Engine Replay.
8. Play cycles, change sensors, orbit the cutaway engine, focus components, use the
   exploded view, and show risk-linked lighting changes.
9. Compare Operations mode (truth hidden) with Evaluation mode (truth/error shown).
10. Run one prediction in Prediction Lab and score a small CSV batch.
11. Open Platform to show pipeline counts, model metrics, latency, logs, and drift state.
12. Call `GET /health` and `POST /predict` from the terminal.
13. Explain branch/PR ownership and the limitations documented in the UI.

## Commands

```bash
docker compose up --build
```

```bash
curl http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  --data @demo/predict_sample.json
```

Run the smoke script:

```bash
PYTHONPATH=src python scripts/smoke_predict.py
```

Generate readiness evidence:

```bash
PYTHONPATH=src python scripts/check_readiness.py
```

## Honest Demo Language

- Say "engine degradation replay" or "C-MAPSS simulation replay," never "live aircraft telemetry."
- The Three.js engine is a conceptual sensor map, not a physical simulation.
- A missing drift result means insufficient production observations, not zero drift.
- Select low-, medium-, and high-risk examples from current model output; do not hardcode an outcome.
