"""Asset upload and serving endpoints."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from localnotion.api.deps import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assets", tags=["assets"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _assets_dir() -> Path:
    s = get_settings()
    d = s.data_dir / "assets"
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("/upload")
async def upload_asset(file: UploadFile = File(...)) -> dict[str, str]:
    """Upload an image file, return its URL."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    # Content-hash filename to avoid duplicates
    digest = hashlib.sha256(data).hexdigest()[:16]
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(file.filename).stem)[:40]
    filename = f"{digest}_{safe_name}{ext}"

    dest = _assets_dir() / filename
    dest.write_bytes(data)
    logger.info("Uploaded asset: %s (%d bytes)", filename, len(data))

    return {"url": f"/api/assets/{filename}", "filename": filename}


@router.get("/{filename}")
async def get_asset(filename: str) -> FileResponse:
    """Serve an uploaded asset."""
    # Sanitize filename to prevent path traversal
    safe = Path(filename).name
    if safe != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = _assets_dir() / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    return FileResponse(path)
