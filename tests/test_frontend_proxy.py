import importlib
import os
import unittest
from unittest.mock import patch

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


def load_proxy_module():
    try:
        return importlib.import_module("industrial_health.api.frontend_proxy")
    except ModuleNotFoundError as exc:
        raise AssertionError("frontend proxy module is missing") from exc


def build_upstream() -> FastAPI:
    upstream = FastAPI()

    @upstream.get("/health")
    def health(detail: str | None = None):
        return {"status": "ready", "model_version": "5", "detail": detail}

    @upstream.post("/predict")
    async def predict(request: Request):
        return {"received": await request.json(), "model_version": "5"}

    @upstream.get("/invalid")
    def invalid():
        return JSONResponse(status_code=422, content={"detail": "invalid request"})

    return upstream


class FrontendProxyTests(unittest.TestCase):
    def build_client(self) -> TestClient:
        module = load_proxy_module()
        transport = httpx.ASGITransport(app=build_upstream())
        return TestClient(
            module.create_frontend_app(
                upstream_url="http://mlops-api",
                transport=transport,
            )
        )

    def test_root_serves_the_existing_vercel_interface(self):
        response = self.build_client().get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("AeroReliability Lab", response.text)
        self.assertIn("/static/js/app.js", response.text)

    def test_default_upstream_is_the_live_komodo_api(self):
        module = load_proxy_module()

        with patch.dict(os.environ, {"MLOPS_BACKEND_URL": ""}):
            app = module.create_frontend_app()

        self.assertEqual(app.state.upstream_url, "http://exp.s3.fsbm.ma:3402")

    def test_get_request_and_query_are_forwarded(self):
        response = self.build_client().get("/health?detail=full")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ready", "model_version": "5", "detail": "full"},
        )

    def test_post_body_is_forwarded(self):
        response = self.build_client().post("/predict", json={"engine_id": "FD004_204"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["received"], {"engine_id": "FD004_204"})
        self.assertEqual(response.json()["model_version"], "5")

    def test_upstream_error_status_is_preserved(self):
        response = self.build_client().get("/invalid")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"detail": "invalid request"})


if __name__ == "__main__":
    unittest.main()
