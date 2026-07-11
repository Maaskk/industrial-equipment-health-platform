import unittest

from fastapi import HTTPException

from industrial_health.api.app import app
from industrial_health.mlops.smoke import build_sample_payload


def route_for(path):
    matches = [route for route in app.routes if getattr(route, "path", None) == path]
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one route for {path}, found {len(matches)}")
    return matches[0]


class MaaskkApiAppTests(unittest.TestCase):
    def test_dashboard_is_served_from_fastapi(self):
        body = route_for("/").endpoint()

        self.assertIn("Industrial Equipment Health Platform", body)
        self.assertIn("Run prediction", body)

    def test_demo_payload_matches_model_contract(self):
        body = route_for("/demo-payload").endpoint()

        self.assertIn("engine_id", body)
        self.assertIn("features", body)
        self.assertGreater(len(body["features"]), 20)

    def test_predict_route_accepts_json_body(self):
        predict_route = route_for("/predict")

        self.assertIsNotNone(predict_route.body_field)

    def test_health_reports_loaded_model_readiness(self):
        body = route_for("/health").endpoint()

        self.assertEqual(body["status"], "ready")
        self.assertTrue(body["model_loaded"])
        self.assertEqual(body["model_source"], "local_pickle")
        self.assertGreater(body["feature_count"], 20)

    def test_predict_accepts_generated_sample_payload(self):
        predict_route = route_for("/predict")
        request_model = predict_route.body_field.field_info.annotation
        payload = request_model(**build_sample_payload())

        body = predict_route.endpoint(payload)

        self.assertIn("remaining_useful_life", body)
        self.assertIn(body["risk_level"], {"low", "medium", "high"})

    def test_predict_rejects_unknown_feature(self):
        payload = build_sample_payload()
        payload["features"] = dict(payload["features"])
        payload["features"]["unknown_sensor"] = 1.0
        predict_route = route_for("/predict")
        request_model = predict_route.body_field.field_info.annotation

        with self.assertRaises(HTTPException) as error:
            predict_route.endpoint(request_model(**payload))

        self.assertEqual(error.exception.status_code, 422)
        self.assertIn("unknown_sensor", str(error.exception.detail))


if __name__ == "__main__":
    unittest.main()
