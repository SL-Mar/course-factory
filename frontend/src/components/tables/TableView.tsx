import { useState, useEffect, useCallback } from "react";
import type { TableDef, TableRow, TableColumn, TableTemplate } from "../../types";
import {
  getTable,
  queryTable,
  insertRow,
  listTables,
  createTable,
  getTableTemplates,
} from "../../api/tables";

interface TableViewProps {
  tableName: string | null;
  onOpenTable: (name: string) => void;
}

type ViewMode = "grid" | "kanban";

export function TableView({ tableName, onOpenTable }: TableViewProps) {
  const [tables, setTables] = useState<TableDef[]>([]);
  const [templates, setTemplates] = useState<TableTemplate[]>([]);
  const [table, setTable] = useState<TableDef | null>(null);
  const [rows, setRows] = useState<TableRow[]>([]);
  const [totalRows, setTotalRows] = useState(0);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [showNewRow, setShowNewRow] = useState(false);
  const [newRowData, setNewRowData] = useState<Record<string, string>>({});
  const [showCreateTable, setShowCreateTable] = useState(false);
  const [newTableName, setNewTableName] = useState("");
  const [kanbanField, setKanbanField] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  // Load tables list
  useEffect(() => {
    listTables()
      .then(setTables)
      .catch(() => setTables([]));
    getTableTemplates()
      .then(setTemplates)
      .catch(() => setTemplates([]));
  }, []);

  const loadTable = useCallback(async () => {
    if (!tableName) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const def = await getTable(tableName);
      setTable(def);

      // Find first select/status column for kanban
      const selectCol = def.columns.find(
        (c) => c.type === "select" || c.type === "status",
      );
      if (selectCol && !kanbanField) {
        setKanbanField(selectCol.name);
      }

      const result = await queryTable(tableName, {
        sort_by: sortBy || undefined,
        sort_order: sortBy ? sortOrder : undefined,
        limit: 100,
      });
      setRows(result.rows);
      setTotalRows(result.total);
    } catch {
      setTable(null);
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [tableName, sortBy, sortOrder, kanbanField]);

  useEffect(() => {
    loadTable();
  }, [loadTable]);

  const handleInsertRow = async () => {
    if (!tableName) return;
    try {
      await insertRow(tableName, newRowData);
      setNewRowData({});
      setShowNewRow(false);
      loadTable();
    } catch (err) {
      console.error("Insert row failed:", err);
    }
  };

  const handleCreateTable = async (template?: TableTemplate) => {
    const name = template ? template.name : newTableName.trim();
    if (!name) return;
    try {
      const columns: TableColumn[] = template
        ? template.columns
        : [
            { name: "Name", type: "text" },
            { name: "Status", type: "select", options: ["Todo", "In Progress", "Done"] },
          ];
      await createTable({ name, columns });
      setShowCreateTable(false);
      setNewTableName("");
      const updated = await listTables();
      setTables(updated);
      onOpenTable(name);
    } catch (err) {
      console.error("Create table failed:", err);
    }
  };

  const toggleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(field);
      setSortOrder("asc");
    }
  };

  // If no table selected, show table list
  if (!tableName) {
    return (
      <div className="h-full overflow-y-auto bg-content">
        <div className="max-w-4xl mx-auto px-8 py-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-content-text">Tables</h1>
              <p className="text-sm text-content-muted mt-0.5">
                {tables.length} tables
              </p>
            </div>
            <button
              onClick={() => setShowCreateTable(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-accent text-white text-sm font-medium rounded-lg hover:bg-accent-hover transition-colors"
            >
              <span className="text-lg leading-none">+</span>
              New Table
            </button>
          </div>

          {/* Create table form */}
          {showCreateTable && (
            <div className="mb-6 p-4 bg-content-secondary rounded-lg border border-content-border animate-fade-in">
              <h3 className="text-sm font-semibold text-content-text mb-3">
                Create New Table
              </h3>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newTableName}
                  onChange={(e) => setNewTableName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleCreateTable();
                  }}
                  placeholder="Table name..."
                  className="flex-1 px-3 py-2 text-sm border border-content-border rounded-md bg-content text-content-text placeholder-content-muted focus:outline-none focus:border-accent"
                  autoFocus
                />
                <button
                  onClick={() => handleCreateTable()}
                  disabled={!newTableName.trim()}
                  className="px-4 py-2 text-sm bg-accent text-white rounded-md hover:bg-accent-hover transition-colors disabled:opacity-40"
                >
                  Create
                </button>
                <button
                  onClick={() => setShowCreateTable(false)}
                  className="px-3 py-2 text-sm text-content-muted hover:text-content-text"
                >
                  Cancel
                </button>
              </div>

              {templates.length > 0 && (
                <>
                  <p className="text-xs text-content-muted mb-2">Or use a template:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {templates.map((tmpl) => (
                      <button
                        key={tmpl.name}
                        onClick={() => handleCreateTable(tmpl)}
                        className="p-3 text-left border border-content-border rounded-md hover:border-accent hover:bg-content-tertiary transition-colors"
                      >
                        <div className="text-sm font-medium text-content-text">
                          {tmpl.name}
                        </div>
                        <div className="text-xs text-content-muted mt-0.5">
                          {tmpl.description}
                        </div>
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Table cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {tables.map((t) => (
              <button
                key={t.name}
                onClick={() => onOpenTable(t.name)}
                className="p-4 text-left border border-content-border rounded-lg bg-content-secondary hover:border-accent hover:shadow-sm transition-all group"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">&#128202;</span>
                  <span className="text-sm font-semibold text-content-text group-hover:text-accent transition-colors">
                    {t.name}
                  </span>
                </div>
                <div className="text-xs text-content-muted">
                  {t.row_count} rows &middot; {t.columns.length} columns
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-content">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!table) {
    return (
      <div className="flex items-center justify-center h-full bg-content text-content-muted text-sm">
        Table not found
      </div>
    );
  }

  // Get kanban groups
  const kanbanColumn = table.columns.find((c) => c.name === kanbanField);
  const kanbanGroups = kanbanColumn?.options || [];

  return (
    <div className="h-full flex flex-col bg-content">
      {/* Header */}
      <div className="px-6 pt-6 pb-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onOpenTable("")}
            className="p-1 rounded hover:bg-content-tertiary transition-colors text-content-muted"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M12 4l-6 6 6 6" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl font-bold text-content-text">{table.name}</h1>
            <p className="text-xs text-content-muted">
              {totalRows} rows &middot; {table.columns.length} columns
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* View mode toggle */}
          <div className="flex bg-content-tertiary rounded-md p-0.5">
            <button
              onClick={() => setViewMode("grid")}
              className={`px-3 py-1 text-xs rounded-md transition-colors ${
                viewMode === "grid"
                  ? "bg-accent text-white"
                  : "text-content-muted hover:text-content-text"
              }`}
            >
              Grid
            </button>
            {kanbanGroups.length > 0 && (
              <button
                onClick={() => setViewMode("kanban")}
                className={`px-3 py-1 text-xs rounded-md transition-colors ${
                  viewMode === "kanban"
                    ? "bg-accent text-white"
                    : "text-content-muted hover:text-content-text"
                }`}
              >
                Kanban
              </button>
            )}
          </div>
          <button
            onClick={() => setShowNewRow(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent text-white text-sm rounded-md hover:bg-accent-hover transition-colors"
          >
            + Row
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto px-6 pb-6">
        {viewMode === "grid" ? (
          /* Grid view */
          <div className="border border-content-border rounded-lg overflow-hidden">
            {/* Header */}
            <div
              className="grid bg-content-secondary border-b border-content-border"
              style={{
                gridTemplateColumns: table.columns
                  .map(() => "1fr")
                  .join(" "),
              }}
            >
              {table.columns.map((col) => (
                <button
                  key={col.name}
                  onClick={() => toggleSort(col.name)}
                  className="px-3 py-2 text-left text-xs font-semibold text-content-muted uppercase tracking-wider hover:text-content-text transition-colors truncate"
                >
                  {col.name}
                  {sortBy === col.name &&
                    (sortOrder === "asc" ? " \u2191" : " \u2193")}
                </button>
              ))}
            </div>

            {/* New row form */}
            {showNewRow && (
              <div
                className="grid border-b border-content-border bg-content-tertiary"
                style={{
                  gridTemplateColumns: table.columns
                    .map(() => "1fr")
                    .join(" "),
                }}
              >
                {table.columns.map((col) => (
                  <div key={col.name} className="px-2 py-1.5">
                    {col.options ? (
                      <select
                        value={newRowData[col.name] || ""}
                        onChange={(e) =>
                          setNewRowData((d) => ({
                            ...d,
                            [col.name]: e.target.value,
                          }))
                        }
                        className="w-full px-2 py-1 text-sm border border-content-border rounded bg-content-secondary text-content-text"
                      >
                        <option value="">--</option>
                        {col.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={col.type === "number" ? "number" : "text"}
                        value={newRowData[col.name] || ""}
                        onChange={(e) =>
                          setNewRowData((d) => ({
                            ...d,
                            [col.name]: e.target.value,
                          }))
                        }
                        placeholder={col.name}
                        className="w-full px-2 py-1 text-sm border border-content-border rounded bg-content-secondary text-content-text placeholder-content-muted focus:outline-none focus:border-accent"
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
            {showNewRow && (
              <div className="flex gap-2 px-3 py-2 bg-content-tertiary border-b border-content-border">
                <button
                  onClick={handleInsertRow}
                  className="px-3 py-1 text-xs bg-accent text-white rounded hover:bg-accent-hover"
                >
                  Insert
                </button>
                <button
                  onClick={() => {
                    setShowNewRow(false);
                    setNewRowData({});
                  }}
                  className="px-3 py-1 text-xs text-content-muted hover:text-content-text"
                >
                  Cancel
                </button>
              </div>
            )}

            {/* Rows */}
            {rows.map((row) => (
              <div
                key={row.id}
                className="grid border-b border-content-border last:border-b-0 hover:bg-content-tertiary transition-colors"
                style={{
                  gridTemplateColumns: table.columns
                    .map(() => "1fr")
                    .join(" "),
                }}
              >
                {table.columns.map((col) => (
                  <div
                    key={col.name}
                    className="px-3 py-2.5 text-sm text-content-text truncate"
                  >
                    {renderCellValue(row[col.name], col)}
                  </div>
                ))}
              </div>
            ))}

            {rows.length === 0 && (
              <div className="px-4 py-8 text-center text-sm text-content-muted">
                No rows yet
              </div>
            )}
          </div>
        ) : (
          /* Kanban view */
          <div className="flex gap-4 h-full overflow-x-auto pb-4">
            {kanbanGroups.map((group) => {
              const groupRows = rows.filter(
                (r) => r[kanbanField] === group,
              );
              return (
                <div
                  key={group}
                  className="kanban-column flex-shrink-0 w-72 bg-content-secondary rounded-lg p-3"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-content-text">
                      {group}
                    </h3>
                    <span className="text-xs text-content-muted bg-content-tertiary px-1.5 py-0.5 rounded-full">
                      {groupRows.length}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {groupRows.map((row) => (
                      <div
                        key={row.id}
                        className="bg-content p-3 rounded-md border border-content-border shadow-sm"
                      >
                        {table.columns
                          .filter((c) => c.name !== kanbanField)
                          .slice(0, 3)
                          .map((col) => (
                            <div key={col.name} className="mb-1 last:mb-0">
                              <span className="text-[10px] text-content-muted uppercase">
                                {col.name}
                              </span>
                              <div className="text-sm text-content-text truncate">
                                {renderCellValue(row[col.name], col)}
                              </div>
                            </div>
                          ))}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function renderCellValue(value: unknown, col: TableColumn): string {
  if (value === null || value === undefined) return "-";
  if (col.type === "date") {
    return new Date(String(value)).toLocaleDateString();
  }
  return String(value);
}
