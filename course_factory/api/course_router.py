"""Course CRUD router."""

from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, HTTPException

from course_factory.api.deps import get_workspace
from course_factory.api.schemas import (
    CourseCreateRequest,
    CourseResponse,
    CourseListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=CourseListResponse)
async def list_courses() -> CourseListResponse:
    """List all courses."""
    ws = get_workspace()
    courses = ws.list_courses()
    return CourseListResponse(courses=courses)


@router.post("", response_model=CourseResponse)
async def create_course(req: CourseCreateRequest) -> CourseResponse:
    """Create a new course and its workspace on disk."""
    course_id = str(uuid.uuid4())
    ws = get_workspace()
    ws.create(
        course_id=course_id,
        title=req.title,
        description=req.description,
        sources=[s.model_dump() for s in req.sources],
    )
    manifest = ws.get_manifest(course_id)
    return CourseResponse(**manifest)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: str) -> CourseResponse:
    """Get course detail."""
    ws = get_workspace()
    try:
        manifest = ws.get_manifest(course_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseResponse(**manifest)


@router.delete("/{course_id}")
async def delete_course(course_id: str) -> dict:
    """Delete course and its workspace."""
    ws = get_workspace()
    try:
        ws.get_manifest(course_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Course not found")
    ws.delete(course_id)
    return {"ok": True}
