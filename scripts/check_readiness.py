from pathlib import Path

from industrial_health.mlops.readiness import ReadinessItem, build_readiness_report


def main() -> None:
    model_path = Path("models/latest/model.pkl")
    schema_path = Path("models/latest/feature_schema.json")
    metrics_path = Path("models/latest/metrics.json")
    report_path = Path("reports/model_metrics/final_evaluation.json")
    demo_path = Path("demo/predict_sample.json")
    report = build_readiness_report(
        output_path=Path("reports/readiness/maaskk-readiness.json"),
        items=[
            ReadinessItem(
                "api_contract",
                Path("src/industrial_health/api/app.py").exists() and Path("docs/api.md").exists(),
                "FastAPI app and API demo guide exist.",
            ),
            ReadinessItem(
                "docker_compose",
                Path("Dockerfile").exists() and Path("docker-compose.yml").exists(),
                "Dockerfile and docker-compose.yml exist.",
            ),
            ReadinessItem(
                "monitoring",
                Path("src/industrial_health/mlops/monitoring.py").exists()
                and Path("src/industrial_health/mlops/drift.py").exists(),
                "Prediction JSONL logging and drift checks exist.",
            ),
            ReadinessItem(
                "mlflow_training_proof",
                report_path.exists() and Path("notebooks/training_executed.ipynb").exists(),
                "Training report and executed proof notebook exist.",
            ),
            ReadinessItem(
                "active_github_actions",
                Path(".github/workflows/ci.yml").exists(),
                "Active workflow exists at .github/workflows/ci.yml.",
            ),
            ReadinessItem(
                "real_model_artifact",
                model_path.exists() and schema_path.exists() and metrics_path.exists() and demo_path.exists(),
                "Local trained model, schema, metrics, and demo payload exist.",
            ),
        ],
    )
    print(f"status={report['status']} ready={report['ready_count']}/{report['total_count']}")
    if report["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
