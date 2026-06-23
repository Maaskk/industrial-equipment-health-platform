from pathlib import Path

from industrial_health.mlops.readiness import ReadinessItem, build_readiness_report


def main() -> None:
    report = build_readiness_report(
        output_path=Path("reports/readiness/maaskk-readiness.json"),
        items=[
            ReadinessItem("api_contract", True, "FastAPI contract modules and tests exist."),
            ReadinessItem("docker_compose", True, "Dockerfile and docker-compose.yml exist."),
            ReadinessItem("monitoring", True, "Prediction JSONL logging and drift checks exist."),
            ReadinessItem("mlflow_registry_contract", True, "Model URI and registry docs exist."),
            ReadinessItem(
                "active_github_actions",
                False,
                "Template exists; activation requires a GitHub credential with workflow scope.",
            ),
            ReadinessItem(
                "real_model_artifact",
                False,
                "Blocked until Mouhcine provides models/latest/model.pkl and schema files.",
            ),
        ],
    )
    print(f"status={report['status']} ready={report['ready_count']}/{report['total_count']}")


if __name__ == "__main__":
    main()

