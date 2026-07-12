"""Vercel-compatible ASGI entrypoint for the full FastAPI application."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

if os.getenv("VERCEL"):
    os.environ.setdefault("PREDICTION_LOG_PATH", "/tmp/prediction_logs.jsonl")

from industrial_health.api.app import app  # noqa: E402


__all__ = ["app"]
