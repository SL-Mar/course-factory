"""SQLite table engine — CRUD for structured data."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from localnotion.tables.models import ColumnDef, TableRow, TableSchema

logger = logging.getLogger(__name__)

_TYPE_MAP = {
    "text": "TEXT",
    "number": "REAL",
    "date": "TEXT",
    "enum": "TEXT",
    "boolean": "INTEGER",
    "url": "TEXT",
    "email": "TEXT",
    "relation": "TEXT",
}


class TableEngine:
    """Manages SQLite-backed structured data tables."""

    def __init__(self, data_dir: Path) -> None:
        self.tables_dir = data_dir / "data" / "tables"
        self.tables_dir.mkdir(parents=True, exist_ok=True)

    def _db_path(self, table_name: str) -> Path:
        safe = table_name.replace("/", "_").replace("\\", "_")
        return self.tables_dir / f"{safe}.db"

    def _connect(self, table_name: str) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path(table_name)), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def create_table(self, schema: TableSchema) -> None:
        """Create a new table from schema definition."""
        conn = self._connect(schema.name)

        cols = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
        for col in schema.columns:
            sql_type = _TYPE_MAP.get(col.type, "TEXT")
            null = "NOT NULL" if col.required else ""
            default = f"DEFAULT {json.dumps(col.default)}" if col.default is not None else ""
            cols.append(f"{col.name} {sql_type} {null} {default}".strip())

        cols.append("page_id TEXT")
        cols.append("created_at TEXT NOT NULL")
        cols.append("modified_at TEXT NOT NULL")

        sql = f"CREATE TABLE IF NOT EXISTS data ({', '.join(cols)})"
        conn.execute(sql)

        # Store schema as metadata
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO _meta (key, value) VALUES (?, ?)",
            ("schema", schema.model_dump_json()),
        )
        conn.execute(
            "INSERT OR REPLACE INTO _meta (key, value) VALUES (?, ?)",
            ("views", json.dumps([v.model_dump() for v in schema.views])),
        )
        conn.commit()
        conn.close()
        logger.info("Created table '%s' with %d columns", schema.name, len(schema.columns))

    def get_schema(self, table_name: str) -> Optional[TableSchema]:
        """Load the schema for a table."""
        db_path = self._db_path(table_name)
        if not db_path.is_file():
            return None
        conn = self._connect(table_name)
        row = conn.execute("SELECT value FROM _meta WHERE key = 'schema'").fetchone()
        conn.close()
        if not row:
            return None
        return TableSchema.model_validate_json(row["value"])

    def insert_row(self, table_name: str, data: dict[str, Any], page_id: str | None = None) -> int:
        """Insert a row and return the row ID."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect(table_name)

        columns = list(data.keys()) + ["page_id", "created_at", "modified_at"]
        values = list(data.values()) + [page_id, now, now]
        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)

        cursor = conn.execute(
            f"INSERT INTO data ({col_names}) VALUES ({placeholders})", values
        )
        conn.commit()
        row_id = cursor.lastrowid or 0
        conn.close()
        return row_id

    def update_row(self, table_name: str, row_id: int, data: dict[str, Any]) -> None:
        """Update a row by ID."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect(table_name)

        sets = [f"{k} = ?" for k in data.keys()] + ["modified_at = ?"]
        values = list(data.values()) + [now, row_id]

        conn.execute(f"UPDATE data SET {', '.join(sets)} WHERE id = ?", values)
        conn.commit()
        conn.close()

    def delete_row(self, table_name: str, row_id: int) -> None:
        """Delete a row by ID."""
        conn = self._connect(table_name)
        conn.execute("DELETE FROM data WHERE id = ?", (row_id,))
        conn.commit()
        conn.close()

    def query(
        self,
        table_name: str,
        where: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_dir: str = "asc",
        limit: int = 200,
        offset: int = 0,
    ) -> list[TableRow]:
        """Query rows with optional filtering, sorting, and pagination."""
        conn = self._connect(table_name)

        clauses: list[str] = []
        params: list[Any] = []
        if where:
            for k, v in where.items():
                clauses.append(f"{k} = ?")
                params.append(v)

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        order_sql = f" ORDER BY {order_by} {order_dir}" if order_by else " ORDER BY id DESC"

        rows = conn.execute(
            f"SELECT * FROM data{where_sql}{order_sql} LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        result = []
        for row in rows:
            d = dict(row)
            result.append(TableRow(
                id=d.pop("id"),
                page_id=d.pop("page_id", None),
                created_at=d.pop("created_at", ""),
                modified_at=d.pop("modified_at", ""),
                data=d,
            ))

        conn.close()
        return result

    def count(self, table_name: str) -> int:
        """Count total rows."""
        conn = self._connect(table_name)
        row = conn.execute("SELECT COUNT(*) AS c FROM data").fetchone()
        conn.close()
        return row["c"] if row else 0

    def delete_table(self, table_name: str) -> None:
        """Delete a table entirely."""
        path = self._db_path(table_name)
        if path.is_file():
            path.unlink()
            logger.info("Deleted table '%s'", table_name)

    def list_tables(self) -> list[str]:
        """List all table names on disk."""
        return [p.stem for p in sorted(self.tables_dir.glob("*.db")) if p.stem != "localnotion"]
