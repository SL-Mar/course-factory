"""FastAPI application for the Course Factory dashboard and REST API."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from course_factory import __version__
from course_factory.api.setup_router import router as setup_router
from course_factory.api.course_router import router as course_router
from course_factory.api.workspace_router import router as workspace_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Course Factory",
    version=__version__,
    description="Transform technical knowledge into publishable courses.",
)

# ---------------------------------------------------------------------------
# CORS - allow all origins in dev mode
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(setup_router)
app.include_router(course_router)
app.include_router(workspace_router)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok", "version": __version__}


# ---------------------------------------------------------------------------
# Static files — SPA fallback (must be last)
# ---------------------------------------------------------------------------
_STATIC_DIR = Path(__file__).resolve().parent / "static"

if _STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=_STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        """Serve the SPA index.html for any unmatched route."""
        file_path = _STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_STATIC_DIR / "index.html")
