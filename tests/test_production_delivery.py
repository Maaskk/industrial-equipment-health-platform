import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class ProductionDeliveryTests(unittest.TestCase):
    def test_production_compose_builds_shared_image_and_uses_persistent_volumes(self):
        compose_path = ROOT / "deploy" / "compose.production.yml"
        compose = yaml.safe_load(compose_path.read_text())

        expected_services = {
            "mlflow",
            "training-init",
            "api",
            "dagster-webserver",
            "dagster-daemon",
            "ops-gateway",
        }
        self.assertEqual(set(compose["services"]), expected_services)

        application_services = expected_services - {"ops-gateway"}
        for service_name in application_services:
            service = compose["services"][service_name]
            self.assertEqual(
                service["image"],
                "${APP_IMAGE:-industrial-equipment-health-platform:latest}",
            )
            self.assertEqual(
                service["build"],
                {"context": "..", "dockerfile": "Dockerfile"},
            )
            self.assertEqual(service["pull_policy"], "never")
            for volume in service.get("volumes", []):
                self.assertFalse(volume.startswith("./"), volume)

        self.assertEqual(compose["services"]["training-init"]["restart"], "no")
        for service_name in ("mlflow", "api", "dagster-webserver"):
            self.assertIn("healthcheck", compose["services"][service_name])

    def test_repository_does_not_declare_unowned_komodo_resources(self):
        resources_path = ROOT / "komodo" / "resources.toml"
        self.assertFalse(resources_path.exists())

    def test_production_training_uses_all_four_cmapss_subsets(self):
        compose_path = ROOT / "deploy" / "compose.production.yml"
        compose_text = compose_path.read_text()

        self.assertIn("TRAIN_SUBSETS: ${TRAIN_SUBSETS:-FD001 FD002 FD003 FD004}", compose_text)

    def test_production_dashboard_links_are_configurable(self):
        compose_path = ROOT / "deploy" / "compose.production.yml"
        compose_text = compose_path.read_text()

        self.assertIn("MLFLOW_PUBLIC_URL:", compose_text)
        self.assertIn("DAGSTER_PUBLIC_URL:", compose_text)

    def test_production_ports_default_to_loopback_and_allow_configurable_bind(self):
        compose_path = ROOT / "deploy" / "compose.production.yml"
        compose = yaml.safe_load(compose_path.read_text())

        expected_ports = {
            "api": "${HOST_BIND_IP:-127.0.0.1}:${API_HOST_PORT:-8000}:8000",
            "ops-gateway": [
                "${HOST_BIND_IP:-127.0.0.1}:${MLFLOW_HOST_PORT:-5000}:3401",
                "${HOST_BIND_IP:-127.0.0.1}:${DAGSTER_HOST_PORT:-3000}:3403",
            ],
        }
        for service_name, expected_port in expected_ports.items():
            expected = expected_port if isinstance(expected_port, list) else [expected_port]
            self.assertEqual(
                compose["services"][service_name]["ports"], expected
            )

        self.assertNotIn("ports", compose["services"]["mlflow"])
        self.assertNotIn("ports", compose["services"]["dagster-webserver"])

    def test_operational_consoles_require_authentication(self):
        gateway_config = (ROOT / "deploy" / "nginx-ops.conf").read_text()
        password_file = (ROOT / "deploy" / "ops.htpasswd").read_text().strip()

        self.assertGreaterEqual(gateway_config.count("auth_basic"), 2)
        self.assertIn("proxy_pass http://mlflow:5000", gateway_config)
        self.assertIn("proxy_pass http://dagster-webserver:3000", gateway_config)
        self.assertRegex(password_file, r"^[a-z][a-z0-9_-]*:\$apr1\$")

    def test_live_frontend_documentation_names_university_deployment_as_primary(self):
        architecture = (ROOT / "docs" / "architecture" / "live-frontend.md").read_text()

        self.assertIn("http://exp.s3.fsbm.ma:3402/", architecture)
        self.assertNotIn("does not provide a second user interface", architecture)

    def test_repository_has_no_external_frontend_deployment_path(self):
        obsolete_paths = {
            ROOT / "app.py",
            ROOT / "src" / "industrial_health" / "api" / "frontend_proxy.py",
            ROOT / "tests" / "test_frontend_proxy.py",
        }

        for path in obsolete_paths:
            self.assertFalse(path.exists(), path)

    def test_docker_context_excludes_local_and_runtime_artifacts(self):
        ignored = {
            line.rstrip("/") for line in (ROOT / ".dockerignore").read_text().splitlines()
        }
        for required in {".git", ".venv", "data", "models", "logs", "warehouse"}:
            self.assertIn(required, ignored)

    def test_ci_uses_isolated_dataops_state_and_scans_secrets(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()

        self.assertIn("mktemp -d", workflow)
        self.assertIn("DLT_DATA_DIR", workflow)
        self.assertIn("gitleaks/gitleaks-action", workflow)

    def test_release_workflow_has_approval_and_live_verification(self):
        workflow_path = ROOT / ".github" / "workflows" / "release.yml"

        self.assertTrue(workflow_path.exists())
        workflow = workflow_path.read_text()
        self.assertIn("environment: production", workflow)
        self.assertIn("/health", workflow)
        verifier = (ROOT / "scripts" / "verify_release.py").read_text()
        self.assertIn('/predict"', verifier)
        self.assertIn("model_source", verifier)


if __name__ == "__main__":
    unittest.main()
