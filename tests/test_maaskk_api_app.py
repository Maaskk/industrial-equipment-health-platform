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
    def test_api_root_returns_service_metadata(self):
        body = route_for("/").endpoint()

        self.assertEqual(body["service"], "industrial-equipment-health-api")
        self.assertEqual(body["status"], "ready")
        self.assertEqual(body["documentation"], "/docs")

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

    def test_frontend_v2_api_routes_are_registered(self):
        paths = {getattr(route, "path", None) for route in app.routes}

        self.assertIn("/api/fleet/summary", paths)
        self.assertIn("/api/engines/{engine_id}/cycle/{cycle}/predict", paths)
        self.assertIn("/api/predict/batch", paths)
        self.assertIn("/api/platform/status", paths)

    def test_operations_mode_does_not_expose_future_truth(self):
        route = route_for("/api/engines/{engine_id}/cycle/{cycle}/predict")
        request_model = route.body_field.field_info.annotation

        body = route.endpoint("FD004_204", 19, request_model(mode="operations"))

        self.assertNotIn("actual_rul", body)
        self.assertNotIn("prediction_error", body)
        self.assertIn(body["risk_level"], {"low", "medium", "high"})
        self.assertEqual(len(body["sensor_profile"]), 21)

    def test_evaluation_mode_exposes_labelled_truth(self):
        route = route_for("/api/engines/{engine_id}/cycle/{cycle}/predict")
        request_model = route.body_field.field_info.annotation

        body = route.endpoint("FD004_204", 19, request_model(mode="evaluation"))

        self.assertIn("actual_rul", body)
        self.assertIn("prediction_error", body)

    def test_invalid_engine_and_short_history_are_rejected(self):
        detail_route = route_for("/api/engines/{engine_id}")
        predict_route = route_for("/api/engines/{engine_id}/cycle/{cycle}/predict")
        request_model = predict_route.body_field.field_info.annotation

        with self.assertRaises(HTTPException) as unknown:
            detail_route.endpoint("FD999_001", None, "operations")
        with self.assertRaises(HTTPException) as short:
            predict_route.endpoint("FD004_204", 3, request_model(mode="operations"))

        self.assertEqual(unknown.exception.status_code, 404)
        self.assertEqual(short.exception.status_code, 422)

    def test_platform_and_maintenance_endpoints_use_real_inputs(self):
        status = route_for("/api/platform/status").endpoint()
        planner = route_for("/api/maintenance/plan")
        request_model = planner.body_field.field_info.annotation
        plan = planner.endpoint(
            request_model(
                predicted_rul=38,
                average_cycles_per_day=3,
                safety_margin_cycles=8,
            )
        )

        self.assertGreater(len(status["pipeline"]), 4)
        self.assertEqual(plan["maximum_cycles_before_service"], 30.0)
        self.assertEqual(plan["estimated_operating_days"], 10.0)


if __name__ == "__main__":
    unittest.main()
