from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles


FORWARDED_REQUEST_HEADERS = {"accept", "content-type"}
FORWARDED_RESPONSE_HEADERS = {"cache-control", "content-type", "etag", "last-modified"}
SUPPORTED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
DEFAULT_UPSTREAM_URL = "http://exp.s3.fsbm.ma:3402"


def create_frontend_app(
    *,
    upstream_url: str | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Serve the existing interface and forward application requests to Komodo."""

    api_url = (
        upstream_url or os.getenv("MLOPS_BACKEND_URL") or DEFAULT_UPSTREAM_URL
    ).rstrip("/")

    frontend_root = Path(__file__).resolve().parent
    template_path = frontend_root / "templates" / "dashboard.html"
    static_path = frontend_root / "static"
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.upstream_url = api_url
    app.mount("/static", StaticFiles(directory=static_path), name="static")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard() -> str:
        return template_path.read_text(encoding="utf-8")

    @app.api_route("/{path:path}", methods=SUPPORTED_METHODS, include_in_schema=False)
    async def forward(path: str, request: Request) -> Response:
        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() in FORWARDED_REQUEST_HEADERS
        }
        try:
            async with httpx.AsyncClient(
                transport=transport,
                timeout=30,
                follow_redirects=False,
            ) as client:
                upstream = await client.request(
                    method=request.method,
                    url=f"{api_url}/{path}",
                    params=request.query_params.multi_items(),
                    headers=headers,
                    content=await request.body(),
                )
        except httpx.RequestError:
            return JSONResponse(
                status_code=503,
                content={"detail": "The prediction service is temporarily unavailable."},
            )

        response_headers: dict[str, Any] = {
            name: value
            for name, value in upstream.headers.items()
            if name.lower() in FORWARDED_RESPONSE_HEADERS
        }
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )

    return app
