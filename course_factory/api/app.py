"""FastAPI application for the Course Factory dashboard and REST API."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from course_factory import __version__

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
# Health
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok", "version": __version__}


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------
@app.get("/api/courses", tags=["courses"])
async def list_courses() -> list[dict[str, Any]]:
    """List all courses.

    TODO: Wire up to the database layer once ``course_factory.db`` is
    implemented.
    """
    # TODO: Replace with actual DB query
    return []


@app.get("/api/courses/{course_id}", tags=["courses"])
async def get_course(course_id: str) -> dict[str, Any]:
    """Get a single course by ID.

    TODO: Fetch from the database and return full course metadata.
    """
    return {"id": course_id, "status": "not_implemented"}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
@app.get("/api/pipeline/{course_id}/status", tags=["pipeline"])
async def pipeline_status(course_id: str) -> dict[str, Any]:
    """Return the current pipeline status for a course.

    TODO: Query the pipeline orchestrator for real-time stage progress.
    """
    return {
        "course_id": course_id,
        "stage": "unknown",
        "progress": 0.0,
        "message": "Pipeline status not yet implemented.",
    }
