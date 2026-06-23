import unittest

from industrial_health.api.app import app


class MaaskkApiAppTests(unittest.TestCase):
    def test_predict_route_accepts_json_body(self):
        predict_routes = [route for route in app.routes if getattr(route, "path", None) == "/predict"]

        self.assertEqual(len(predict_routes), 1)
        self.assertIsNotNone(predict_routes[0].body_field)


if __name__ == "__main__":
    unittest.main()

