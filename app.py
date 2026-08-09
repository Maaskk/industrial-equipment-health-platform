"""Vercel entrypoint for the public application."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from industrial_health.api.frontend_proxy import create_frontend_app  # noqa: E402


app = create_frontend_app()


__all__ = ["app"]
