"""SQLite page index — metadata cache rebuilt from frontmatter."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from localnotion.core.models import Page, PageSummary, BacklinkEntry

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS page_index (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    parent_id TEXT,
    type TEXT DEFAULT 'page',
    status TEXT DEFAULT 'draft',
    tags TEXT,
    links TEXT,
    workspace TEXT DEFAULT 'default',
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0,
    icon TEXT DEFAULT '',
    cover TEXT DEFAULT '',
    is_favorite INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_page_workspace ON page_index(workspace);
CREATE INDEX IF NOT EXISTS idx_page_type ON page_index(type);
CREATE INDEX IF NOT EXISTS idx_page_parent ON page_index(parent_id);
CREATE INDEX IF NOT EXISTS idx_page_deleted ON page_index(is_deleted);
CREATE INDEX IF NOT EXISTS idx_page_favorite ON page_index(is_favorite);

CREATE TABLE IF NOT EXISTS backlinks (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    context TEXT DEFAULT '',
    PRIMARY KEY (source_id, target_id)
);

CREATE INDEX IF NOT EXISTS idx_backlink_target ON backlinks(target_id);

CREATE TABLE IF NOT EXISTS engine_runs (
    run_id TEXT PRIMARY KEY,
    engine TEXT NOT NULL,
    status TEXT NOT NULL,
    input_pages TEXT,
    output_pages TEXT,
    llm_model TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    started_at TEXT,
    completed_at TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS table_registry (
    name TEXT PRIMARY KEY,
    display_name TEXT,
    schema_def TEXT NOT NULL,
    default_view TEXT DEFAULT 'table',
    db_path TEXT NOT NULL,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS workspace_meta (
    name TEXT PRIMARY KEY,
    icon TEXT DEFAULT '',
    color TEXT DEFAULT '#2383e2',
    sort_order INTEGER DEFAULT 0
);
"""


class PageIndex:
    """SQLite-backed metadata index for fast queries without reading every .md file."""

    def __init__(self, data_dir: Path) -> None:
        self.db_path = data_dir / "data" / "localnotion.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        # Migrate: add cover column if missing (existing DBs)
        try:
            self._conn.execute("ALTER TABLE page_index ADD COLUMN cover TEXT DEFAULT ''")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        # Migrate: add sort_order column if missing (existing DBs)
        try:
            self._conn.execute("ALTER TABLE page_index ADD COLUMN sort_order INTEGER DEFAULT 0")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------
    # Upsert / Delete
    # ------------------------------------------------------------------

    def upsert_page(self, page: Page) -> None:
        """Insert or replace page metadata in the index."""
        self._conn.execute(
            """INSERT OR REPLACE INTO page_index
               (id, title, parent_id, type, status, tags, links, workspace,
                created_at, modified_at, word_count, is_deleted, icon, cover, is_favorite, sort_order)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                page.id,
                page.title,
                page.parent_id,
                page.type,
                page.status,
                json.dumps(page.tags),
                json.dumps(page.links),
                page.workspace,
                page.created_at.isoformat(),
                page.modified_at.isoformat(),
                page.word_count,
                int(page.is_deleted),
                page.icon,
                page.cover,
                int(page.is_favorite),
                page.sort_order,
            ),
        )
        self._rebuild_backlinks(page)
        self._conn.commit()

    def remove_page(self, page_id: str) -> None:
        """Remove a page from the index entirely."""
        self._conn.execute("DELETE FROM page_index WHERE id = ?", (page_id,))
        self._conn.execute("DELETE FROM backlinks WHERE source_id = ?", (page_id,))
        self._conn.commit()

    def _rebuild_backlinks(self, page: Page) -> None:
        """Rebuild outgoing backlinks for a page."""
        self._conn.execute("DELETE FROM backlinks WHERE source_id = ?", (page.id,))
        for target_id in page.links:
            self._conn.execute(
                "INSERT OR IGNORE INTO backlinks (source_id, target_id, context) VALUES (?,?,?)",
                (page.id, target_id, ""),
            )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_page_summary(self, page_id: str) -> Optional[PageSummary]:
        row = self._conn.execute(
            "SELECT * FROM page_index WHERE id = ?", (page_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_summary(row)

    def list_pages(
        self,
        workspace: Optional[str] = None,
        page_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        include_deleted: bool = False,
        favorites_only: bool = False,
        limit: int = 200,
        offset: int = 0,
    ) -> list[PageSummary]:
        clauses: list[str] = []
        params: list = []

        if not include_deleted:
            clauses.append("is_deleted = 0")
        if workspace:
            clauses.append("workspace = ?")
            params.append(workspace)
        if page_type:
            clauses.append("type = ?")
            params.append(page_type)
        if parent_id is not None:
            clauses.append("parent_id = ?")
            params.append(parent_id)
        if favorites_only:
            clauses.append("is_favorite = 1")

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM page_index{where} ORDER BY sort_order ASC, modified_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_summary(r) for r in rows]

    def search_titles(self, query: str, limit: int = 50) -> list[PageSummary]:
        rows = self._conn.execute(
            "SELECT * FROM page_index WHERE is_deleted = 0 AND title LIKE ? ORDER BY modified_at DESC LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        return [self._row_to_summary(r) for r in rows]

    def get_recent(self, limit: int = 20) -> list[PageSummary]:
        rows = self._conn.execute(
            "SELECT * FROM page_index WHERE is_deleted = 0 ORDER BY modified_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_summary(r) for r in rows]

    def get_backlinks(self, page_id: str) -> list[BacklinkEntry]:
        rows = self._conn.execute(
            """SELECT b.source_id, p.title AS source_title, b.context
               FROM backlinks b
               JOIN page_index p ON p.id = b.source_id
               WHERE b.target_id = ?""",
            (page_id,),
        ).fetchall()
        return [
            BacklinkEntry(
                source_id=r["source_id"],
                source_title=r["source_title"],
                context=r["context"],
            )
            for r in rows
        ]

    def get_children(self, parent_id: str) -> list[PageSummary]:
        rows = self._conn.execute(
            "SELECT * FROM page_index WHERE parent_id = ? AND is_deleted = 0 ORDER BY title",
            (parent_id,),
        ).fetchall()
        return [self._row_to_summary(r) for r in rows]

    def get_workspaces(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT workspace FROM page_index WHERE is_deleted = 0 ORDER BY workspace"
        ).fetchall()
        return [r["workspace"] for r in rows]

    def get_orphans(self) -> list[PageSummary]:
        """Pages with no incoming or outgoing links."""
        rows = self._conn.execute(
            """SELECT * FROM page_index
               WHERE is_deleted = 0
                 AND id NOT IN (SELECT source_id FROM backlinks)
                 AND id NOT IN (SELECT target_id FROM backlinks)
               ORDER BY modified_at DESC""",
        ).fetchall()
        return [self._row_to_summary(r) for r in rows]

    def count_pages(self, workspace: Optional[str] = None) -> int:
        if workspace:
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM page_index WHERE is_deleted = 0 AND workspace = ?",
                (workspace,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM page_index WHERE is_deleted = 0"
            ).fetchone()
        return row["c"] if row else 0

    def batch_reorder(self, page_ids: list[str], workspace: str | None = None) -> int:
        """Set sort_order for a list of page IDs based on their position in the list.

        If workspace is provided, also moves all pages to that workspace.
        Returns the number of pages updated.
        """
        updated = 0
        for idx, pid in enumerate(page_ids):
            if workspace is not None:
                self._conn.execute(
                    "UPDATE page_index SET sort_order = ?, workspace = ? WHERE id = ?",
                    (idx, workspace, pid),
                )
            else:
                self._conn.execute(
                    "UPDATE page_index SET sort_order = ? WHERE id = ?",
                    (idx, pid),
                )
            updated += 1
        self._conn.commit()
        return updated

    # ------------------------------------------------------------------
    # Rebuild
    # ------------------------------------------------------------------

    def rebuild_from_pages(self, pages: list[Page]) -> int:
        """Drop and rebuild the index from a list of pages."""
        self._conn.execute("DELETE FROM page_index")
        self._conn.execute("DELETE FROM backlinks")
        for page in pages:
            self.upsert_page(page)
        self._conn.commit()
        logger.info("Rebuilt index with %d pages", len(pages))
        return len(pages)

    # ------------------------------------------------------------------
    # Engine runs
    # ------------------------------------------------------------------

    def save_engine_run(self, run: dict) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO engine_runs
               (run_id, engine, status, input_pages, output_pages,
                llm_model, tokens_used, cost_usd, started_at, completed_at, error)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                run["run_id"],
                run["engine"],
                run["status"],
                json.dumps(run.get("input_pages", [])),
                json.dumps(run.get("output_pages", [])),
                run.get("llm_model", ""),
                run.get("tokens_used", 0),
                run.get("cost_usd", 0.0),
                run.get("started_at", ""),
                run.get("completed_at", ""),
                run.get("error", ""),
            ),
        )
        self._conn.commit()

    def list_engine_runs(self, engine: Optional[str] = None, limit: int = 50) -> list[dict]:
        if engine:
            rows = self._conn.execute(
                "SELECT * FROM engine_runs WHERE engine = ? ORDER BY started_at DESC LIMIT ?",
                (engine, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM engine_runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Table registry
    # ------------------------------------------------------------------

    def register_table(self, name: str, display_name: str, schema_def: dict, db_path: str) -> None:
        from datetime import datetime, timezone

        self._conn.execute(
            """INSERT OR REPLACE INTO table_registry
               (name, display_name, schema_def, db_path, created_at)
               VALUES (?,?,?,?,?)""",
            (name, display_name, json.dumps(schema_def), db_path, datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()

    def list_tables(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM table_registry ORDER BY display_name").fetchall()
        return [dict(r) for r in rows]

    def get_table_info(self, name: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM table_registry WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Workspace metadata
    # ------------------------------------------------------------------

    def upsert_workspace_meta(self, name: str, icon: str = "", color: str = "#2383e2", sort_order: int = 0) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO workspace_meta (name, icon, color, sort_order) VALUES (?,?,?,?)",
            (name, icon, color, sort_order),
        )
        self._conn.commit()

    def list_workspace_meta(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM workspace_meta ORDER BY sort_order, name"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_workspace_meta(self, name: str) -> None:
        self._conn.execute("DELETE FROM workspace_meta WHERE name = ?", (name,))
        self._conn.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_summary(row: sqlite3.Row) -> PageSummary:
        from datetime import datetime

        return PageSummary(
            id=row["id"],
            title=row["title"],
            type=row["type"],
            status=row["status"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            workspace=row["workspace"],
            parent_id=row["parent_id"],
            icon=row["icon"] or "",
            cover=row["cover"] or "",
            is_favorite=bool(row["is_favorite"]),
            is_deleted=bool(row["is_deleted"]),
            word_count=row["word_count"],
            sort_order=row["sort_order"] if "sort_order" in row.keys() else 0,
            created_at=datetime.fromisoformat(row["created_at"]),
            modified_at=datetime.fromisoformat(row["modified_at"]),
        )
