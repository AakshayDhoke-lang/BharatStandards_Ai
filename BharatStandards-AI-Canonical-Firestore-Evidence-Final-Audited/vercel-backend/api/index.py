"""Vercel ASGI entrypoint for BharatStandards AI.

Do not add analysis logic here. The production function imports the exact same
FastAPI application used by local development, so the parser -> AI extractor ->
product compatibility -> matcher -> result pipeline remains single-source.
"""

from app.main import app

__all__ = ["app"]
