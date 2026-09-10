"""Vercel Serverless Function Entrypoint for AegisShield Platform."""
import os
import sys
from pathlib import Path

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from starlette.types import ASGIApp, Scope, Receive, Send
from app.main import app


class VercelPathFixMiddleware:
    """Normalizes rewritten paths on Vercel so FastAPI routers match correctly."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            # If Vercel rewrites incoming requests to /api/index.py
            if path in ("/api/index.py", "/api/index", "/api"):
                scope["path"] = "/"
            elif path.startswith("/api/index.py/"):
                scope["path"] = path[len("/api/index.py"):]
            elif path.startswith("/api/"):
                # Also allow /api/predict -> /predict if called via API prefix
                sub = path[4:]
                if not sub.startswith("/static"):
                    scope["path"] = sub
        await self.app(scope, receive, send)


app.add_middleware(VercelPathFixMiddleware)
