import unittest

from industrial_health.api import contracts


class ServiceInfoTests(unittest.TestCase):
    def test_root_metadata_identifies_api_and_documentation(self):
        self.assertTrue(hasattr(contracts, "build_service_info"))
        body = contracts.build_service_info()

        self.assertEqual(body["service"], "industrial-equipment-health-api")
        self.assertEqual(body["status"], "ready")
        self.assertEqual(body["documentation"], "/docs")


if __name__ == "__main__":
    unittest.main()
