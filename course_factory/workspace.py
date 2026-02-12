"""Workspace manager — on-disk file tree for each course."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_DIR = Path.home() / ".config" / "course-factory"

STAGE_DIRS = [
    "01-knowledge",
    "02-discovery",
    "03-research",
    "04-synthesis",
    "05-production",
    "06-media",
    "07-qa",
    "08-publish",
]


class WorkspaceManager:
    """CRUD operations for course workspaces on disk.

    Each course lives at ``{workspaces_root}/{course_id}/`` with a
    ``course.json`` manifest and numbered stage directories.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        root = config_dir or _DEFAULT_CONFIG_DIR
        self.workspaces_root = root / "workspaces"
        self.workspaces_root.mkdir(parents=True, exist_ok=True)

    def _course_dir(self, course_id: str) -> Path:
        safe = course_id.replace("/", "_").replace("\\", "_")
        return self.workspaces_root / safe

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        course_id: str,
        title: str,
        description: str = "",
        sources: list[dict[str, Any]] | None = None,
    ) -> Path:
        """Create workspace directories and ``course.json`` manifest."""
        course_dir = self._course_dir(course_id)
        course_dir.mkdir(parents=True, exist_ok=True)

        for stage_dir in STAGE_DIRS:
            (course_dir / stage_dir).mkdir(exist_ok=True)

        manifest = {
            "id": course_id,
            "title": title,
            "description": description,
            "sources": sources or [],
        }
        (course_dir / "course.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        logger.info("Created workspace for course %s at %s", course_id, course_dir)
        return course_dir

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_manifest(self, course_id: str) -> dict[str, Any]:
        """Read the course.json manifest."""
        manifest_path = self._course_dir(course_id) / "course.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"No manifest for course {course_id}")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def get_tree(self, course_id: str) -> list[dict[str, Any]]:
        """Return a recursive file-tree structure for the workspace."""
        course_dir = self._course_dir(course_id)
        if not course_dir.is_dir():
            raise FileNotFoundError(f"No workspace for course {course_id}")
        return self._build_tree(course_dir, course_dir)

    def read_file(self, course_id: str, rel_path: str) -> str:
        """Read a file from the workspace.  Guards against path traversal."""
        course_dir = self._course_dir(course_id)
        target = (course_dir / rel_path).resolve()
        if not str(target).startswith(str(course_dir.resolve())):
            raise PermissionError("Path traversal not allowed")
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {rel_path}")
        return target.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write_file(self, course_id: str, rel_path: str, content: str) -> None:
        """Write content to a file inside the workspace."""
        course_dir = self._course_dir(course_id)
        target = (course_dir / rel_path).resolve()
        if not str(target).startswith(str(course_dir.resolve())):
            raise PermissionError("Path traversal not allowed")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, course_id: str) -> None:
        """Remove an entire workspace from disk."""
        course_dir = self._course_dir(course_id)
        if course_dir.is_dir():
            shutil.rmtree(course_dir)
            logger.info("Deleted workspace for course %s", course_id)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_courses(self) -> list[dict[str, Any]]:
        """Return manifests for all courses on disk."""
        results: list[dict[str, Any]] = []
        if not self.workspaces_root.is_dir():
            return results
        for child in sorted(self.workspaces_root.iterdir()):
            manifest = child / "course.json"
            if manifest.is_file():
                try:
                    results.append(json.loads(manifest.read_text(encoding="utf-8")))
                except (json.JSONDecodeError, OSError):
                    logger.warning("Skipping corrupt manifest in %s", child)
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_tree(root: Path, base: Path) -> list[dict[str, Any]]:
        """Recursively build a list of ``FileNode`` dicts."""
        nodes: list[dict[str, Any]] = []
        for child in sorted(root.iterdir()):
            rel = str(child.relative_to(base))
            if child.is_dir():
                nodes.append(
                    {
                        "name": child.name,
                        "path": rel,
                        "type": "directory",
                        "children": WorkspaceManager._build_tree(child, base),
                    }
                )
            else:
                nodes.append(
                    {
                        "name": child.name,
                        "path": rel,
                        "type": "file",
                    }
                )
        return nodes
