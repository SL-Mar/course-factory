import { useState, useEffect, useCallback } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPlus, faGripVertical } from "@fortawesome/free-solid-svg-icons";
import type { WorkspaceMeta, View } from "../../types";
import { getWorkspaceMeta, createWorkspaceMeta, reorderWorkspaces } from "../../api/pages";
import { WorkspaceIcon, ICON_KEYS } from "../shared/WorkspaceIcon";

interface HomeViewProps {
  onSelectWorkspace: (workspace: string) => void;
  onNavigate: (view: View) => void;
}

const DEFAULT_COLORS = [
  "#2383e2", "#7c3aed", "#059669", "#dc2626",
  "#d97706", "#0891b2", "#4f46e5", "#be185d",
  "#65a30d", "#0d9488", "#ea580c",
];

export function HomeView({ onSelectWorkspace, onNavigate }: HomeViewProps) {
  const [workspaces, setWorkspaces] = useState<WorkspaceMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // Drag state
  const [dragName, setDragName] = useState<string | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);

  const loadWorkspaces = useCallback(async () => {
    try {
      const data = await getWorkspaceMeta();
      setWorkspaces(data);
    } catch {
      setWorkspaces([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWorkspaces();
  }, [loadWorkspaces]);

  const handleTileClick = (ws: WorkspaceMeta) => {
    if (dragName) return; // don't navigate during drag
    onSelectWorkspace(ws.name);
    onNavigate("pages");
  };

  const handleDragStart = useCallback((e: React.DragEvent, wsName: string) => {
    setDragName(wsName);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", wsName);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDragName(null);
    setDropIndex(null);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, idx: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDropIndex(idx);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent, targetIdx: number) => {
    e.preventDefault();
    const wsName = e.dataTransfer.getData("text/plain");
    if (!wsName) return;

    const currentIdx = workspaces.findIndex(w => w.name === wsName);
    if (currentIdx === -1 || currentIdx === targetIdx) {
      setDragName(null);
      setDropIndex(null);
      return;
    }

    // Compute new order
    const newList = [...workspaces];
    const [moved] = newList.splice(currentIdx, 1);
    newList.splice(targetIdx, 0, moved);

    // Reset drag state
    setDragName(null);
    setDropIndex(null);

    // Optimistic update
    setWorkspaces(newList);

    // Persist
    try {
      await reorderWorkspaces(newList.map(w => w.name));
    } catch (err) {
      console.error("Workspace reorder failed:", err);
      loadWorkspaces(); // rollback
    }
  }, [workspaces, loadWorkspaces]);

  const totalPages = workspaces.reduce((sum, ws) => sum + ws.page_count, 0);

  return (
    <div className="h-full flex flex-col bg-content overflow-y-auto">
      {/* Header */}
      <div className="px-8 pt-10 pb-6">
        <h1 className="text-2xl font-semibold text-content-text">
          Welcome to Katja
        </h1>
        <p className="text-sm text-content-muted mt-1">
          {totalPages} pages across {workspaces.length} workspaces
        </p>
      </div>

      {/* Tile Grid */}
      <div className="px-8 pb-10">
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {workspaces.map((ws, idx) => {
              const isDragging = dragName === ws.name;
              const isDropTarget = dropIndex === idx && dragName !== null && dragName !== ws.name;

              return (
                <div
                  key={ws.name}
                  draggable
                  onDragStart={(e) => handleDragStart(e, ws.name)}
                  onDragEnd={handleDragEnd}
                  onDragOver={(e) => handleDragOver(e, idx)}
                  onDrop={(e) => handleDrop(e, idx)}
                  onClick={() => handleTileClick(ws)}
                  className={`home-tile group relative flex flex-col items-start p-5 rounded-xl border transition-all duration-200 text-left min-h-[120px] cursor-grab active:cursor-grabbing ${
                    isDropTarget
                      ? "border-accent ring-2 ring-accent/30"
                      : "border-content-border/50 hover:border-accent/40"
                  } ${isDragging ? "opacity-40" : ""} bg-content-secondary`}
                  style={{
                    background: isDropTarget
                      ? undefined
                      : `linear-gradient(135deg, ${ws.color}12 0%, ${ws.color}06 100%)`,
                  }}
                >
                  {/* Grip handle */}
                  <span className="absolute top-3 left-3 opacity-0 group-hover:opacity-40 transition-opacity text-content-muted">
                    <FontAwesomeIcon icon={faGripVertical} size="xs" />
                  </span>
                  {/* Icon */}
                  <span className="mb-3" style={{ color: ws.color }}>
                    <WorkspaceIcon icon={ws.icon} size="lg" />
                  </span>
                  {/* Name */}
                  <span className="text-sm font-medium text-content-text capitalize group-hover:text-accent-light transition-colors">
                    {ws.name}
                  </span>
                  {/* Count badge */}
                  <span
                    className="absolute top-4 right-4 text-xs font-medium px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor: `${ws.color}20`,
                      color: ws.color,
                    }}
                  >
                    {ws.page_count}
                  </span>
                  {/* Bottom accent bar */}
                  <div
                    className="absolute bottom-0 left-4 right-4 h-0.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ backgroundColor: ws.color }}
                  />
                </div>
              );
            })}

            {/* Add workspace tile */}
            <button
              onClick={() => setShowModal(true)}
              className="home-tile flex flex-col items-center justify-center p-5 rounded-xl border border-dashed border-content-border/60 hover:border-accent/40 bg-content-secondary/50 transition-all duration-200 min-h-[120px]"
            >
              <FontAwesomeIcon icon={faPlus} className="text-content-faint mb-1" size="lg" />
              <span className="text-xs text-content-muted">New Workspace</span>
            </button>
          </div>
        )}
      </div>

      {/* Create Workspace Modal */}
      {showModal && (
        <CreateWorkspaceModal
          onClose={() => setShowModal(false)}
          onCreated={() => {
            setShowModal(false);
            loadWorkspaces();
          }}
          existingCount={workspaces.length}
        />
      )}
    </div>
  );
}

/* ── Create Workspace Modal ── */

interface CreateModalProps {
  onClose: () => void;
  onCreated: () => void;
  existingCount: number;
}

function CreateWorkspaceModal({ onClose, onCreated, existingCount }: CreateModalProps) {
  const [name, setName] = useState("");
  const [icon, setIcon] = useState("folder");
  const [color, setColor] = useState(DEFAULT_COLORS[existingCount % DEFAULT_COLORS.length]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim().toLowerCase().replace(/\s+/g, "-");
    if (!trimmed) {
      setError("Name is required");
      return;
    }
    if (trimmed.length > 50) {
      setError("Name too long (max 50 chars)");
      return;
    }
    setSaving(true);
    try {
      await createWorkspaceMeta({
        name: trimmed,
        icon,
        color,
        sort_order: existingCount,
      });
      onCreated();
    } catch {
      setError("Failed to create workspace");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center search-backdrop" onClick={onClose}>
      <div
        className="bg-content-secondary border border-content-border rounded-xl p-6 w-[380px] animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-semibold text-content-text mb-4">
          New Workspace
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-xs text-content-muted mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => { setName(e.target.value); setError(""); }}
              className="w-full px-3 py-2 text-sm bg-content border border-content-border rounded text-content-text focus:outline-none focus:border-accent"
              placeholder="e.g. research, trading..."
              autoFocus
            />
          </div>

          {/* Icon picker — FA icons */}
          <div>
            <label className="block text-xs text-content-muted mb-1">Icon</label>
            <div className="flex flex-wrap gap-1.5">
              {ICON_KEYS.map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setIcon(key)}
                  className={`w-8 h-8 flex items-center justify-center rounded transition-colors ${
                    icon === key
                      ? "bg-accent/20 ring-1 ring-accent text-accent"
                      : "text-content-muted hover:bg-content-tertiary"
                  }`}
                  title={key}
                >
                  <WorkspaceIcon icon={key} size="sm" />
                </button>
              ))}
            </div>
          </div>

          {/* Color picker */}
          <div>
            <label className="block text-xs text-content-muted mb-1">Color</label>
            <div className="flex flex-wrap gap-2">
              {DEFAULT_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setColor(c)}
                  className={`w-7 h-7 rounded-full transition-transform ${
                    color === c ? "ring-2 ring-white/50 scale-110" : "hover:scale-105"
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>

          {error && (
            <p className="text-xs text-red-400">{error}</p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 text-xs text-content-muted hover:text-content-text transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-1.5 text-xs bg-accent text-white rounded hover:bg-accent-hover transition-colors disabled:opacity-50"
            >
              {saving ? "Creating..." : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
