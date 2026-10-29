"""Require a usable selected backend before exposing a healthy HTTP server."""
from main import app
from backends.factory import get_backend
from config import settings


@app.on_event("startup")
async def require_selected_backend():
    # Upstream logs initialization errors and continues. In an add-on a missing
    # Coral/model must fail startup, not report a healthy but unusable service.
    get_backend(settings.DEFAULT_BACKEND)
