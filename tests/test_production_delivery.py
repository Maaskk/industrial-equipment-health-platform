import tomllib
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class ProductionDeliveryTests(unittest.TestCase):
    def test_production_compose_uses_published_image_and_persistent_volumes(self):
        compose_path = ROOT / "deploy" / "compose.production.yml"
        compose = yaml.safe_load(compose_path.read_text())

        expected_services = {
            "mlflow",
            "training-init",
            "api",
            "dagster-webserver",
            "dagster-daemon",
        }
        self.assertEqual(set(compose["services"]), expected_services)

        for service in compose["services"].values():
            self.assertEqual(
                service["image"],
                "${APP_IMAGE:-industrial-equipment-health-platform:latest}",
            )
            self.assertNotIn("build", service)
            for volume in service.get("volumes", []):
                self.assertFalse(volume.startswith("./"), volume)

        self.assertEqual(compose["services"]["training-init"]["restart"], "no")
        for service_name in ("mlflow", "api", "dagster-webserver"):
            self.assertIn("healthcheck", compose["services"][service_name])

    def test_komodo_resources_cover_delivery_and_operations(self):
        resources_path = ROOT / "komodo" / "resources.toml"
        resources = tomllib.loads(resources_path.read_text())

        required = {"server", "builder", "repo", "build", "stack", "procedure", "action"}
        self.assertTrue(required.issubset(resources), set(resources))

        stack = resources["stack"][0]
        self.assertEqual(stack["name"], "industrial-equipment-health-platform")
        self.assertEqual(stack["config"]["server"], "oussama-macbook")
        self.assertEqual(stack["config"]["file_paths"], ["deploy/compose.production.yml"])
        self.assertIn("training-init", stack["config"]["ignore_services"])
        self.assertTrue(stack["config"]["send_alerts"])

        action = resources["action"][0]
        self.assertTrue(action["config"]["schedule_enabled"])
        self.assertEqual(action["config"]["schedule_timezone"], "Africa/Casablanca")

    def test_production_ports_are_loopback_only_and_configurable(self):
        compose_path = ROOT / "deploy" / "compose.production.yml"
        compose = yaml.safe_load(compose_path.read_text())

        expected_ports = {
            "mlflow": "127.0.0.1:${MLFLOW_HOST_PORT:-5000}:5000",
            "api": "127.0.0.1:${API_HOST_PORT:-8000}:8000",
            "dagster-webserver": "127.0.0.1:${DAGSTER_HOST_PORT:-3000}:3000",
        }
        for service_name, expected_port in expected_ports.items():
            self.assertEqual(
                compose["services"][service_name]["ports"], [expected_port]
            )

    def test_docker_context_excludes_local_and_runtime_artifacts(self):
        ignored = {
            line.rstrip("/") for line in (ROOT / ".dockerignore").read_text().splitlines()
        }
        for required in {".git", ".venv", "data", "models", "logs", "warehouse"}:
            self.assertIn(required, ignored)


if __name__ == "__main__":
    unittest.main()
