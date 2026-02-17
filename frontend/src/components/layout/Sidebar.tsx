import { useState, useEffect, useRef, useCallback } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faChevronRight,
  faChevronLeft,
  faMagnifyingGlass,
  faHouse,
  faFile,
  faDiagramProject,
  faComments,
  faGear,
  faTrashCan,
  faTable,
  faPlus,
  faStar,
  faDownload,
  faFilePdf,
  faGripVertical,
} from "@fortawesome/free-solid-svg-icons";
import type { View, Page, TableDef, WorkspaceMeta } from "../../types";
import {
  getRecentPages,
  listPages,
  createPage,
  updatePage,
  getWorkspaceMeta,
  exportPageMd,
  exportPagePdf,
  reorderPages,
  reorderWorkspaces,
} from "../../api/pages";
import { listTables } from "../../api/tables";
import { WorkspaceIcon } from "../shared/WorkspaceIcon";

const SIDEBAR_WIDTH = 420;

interface SidebarProps {
  currentView: View;
  activeWorkspace: string;
  collapsed: boolean;
  refreshKey: number;
  onNavigate: (view: View) => void;
  onOpenPage: (page: Page) => void;
  onOpenTable: (name: string) => void;
  onSetWorkspace: (workspace: string) => void;
  onToggle: () => void;
  onOpenSearch: () => void;
}

interface SectionState {
  favorites: boolean;
  tables: boolean;
  recent: boolean;
  [key: string]: boolean;
}

/* ── Icon shorthand ── */
const Fa = FontAwesomeIcon;

export function Sidebar({
  currentView,
  activeWorkspace,
  collapsed,
  refreshKey,
  onNavigate,
  onOpenPage,
  onOpenTable,
  onSetWorkspace,
  onToggle,
  onOpenSearch,
}: SidebarProps) {
  const [workspaceMeta, setWorkspaceMeta] = useState<WorkspaceMeta[]>([]);
  const [workspacePages, setWorkspacePages] = useState<Record<string, Page[]>>({});
  const [favorites, setFavorites] = useState<Page[]>([]);
  const [recentPages, setRecentPages] = useState<Page[]>([]);
  const [tables, setTables] = useState<TableDef[]>([]);
  const [sections, setSections] = useState<SectionState>({
    favorites: true,
    tables: true,
    recent: false,
  });

  // Fixed sidebar width

  // Drag-and-drop state
  const [dragPageId, setDragPageId] = useState<string | null>(null);
  const [dragSourceWs, setDragSourceWs] = useState<string | null>(null);
  const [dropTargetWs, setDropTargetWs] = useState<string | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);

  // Workspace drag-and-drop state
  const [dragWsName, setDragWsName] = useState<string | null>(null);
  const [dropWsIndex, setDropWsIndex] = useState<number | null>(null);

  const handleDragStart = useCallback((e: React.DragEvent, page: Page) => {
    setDragPageId(page.id);
    setDragSourceWs(page.workspace);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", page.id);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDragPageId(null);
    setDragSourceWs(null);
    setDropTargetWs(null);
    setDropIndex(null);
  }, []);

  const handleDragOverPage = useCallback((e: React.DragEvent, wsName: string, idx: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDropTargetWs(wsName);
    // Determine if drop should be above or below this item
    const rect = e.currentTarget.getBoundingClientRect();
    const midY = rect.top + rect.height / 2;
    setDropIndex(e.clientY < midY ? idx : idx + 1);
  }, []);

  const handleDragOverWsHeader = useCallback((e: React.DragEvent, wsName: string) => {
    if (e.dataTransfer.types.includes("application/x-workspace")) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDropTargetWs(wsName);
    setDropIndex(0); // drop at top of workspace
  }, []);

  const handleDragLeave = useCallback(() => {
    setDropTargetWs(null);
    setDropIndex(null);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent, targetWs: string) => {
    if (e.dataTransfer.types.includes("application/x-workspace")) return;
    e.preventDefault();
    const pageId = e.dataTransfer.getData("text/plain");
    if (!pageId) return;

    const sourceWs = dragSourceWs;
    const targetIdx = dropIndex ?? 0;

    // Reset drag state
    setDragPageId(null);
    setDragSourceWs(null);
    setDropTargetWs(null);
    setDropIndex(null);

    // Build new page order for the target workspace
    const targetPages = [...(workspacePages[targetWs] || [])];
    const isMoving = sourceWs !== targetWs;

    if (isMoving) {
      // Remove from source workspace (optimistic)
      const sourcePages = (workspacePages[sourceWs!] || []).filter(p => p.id !== pageId);
      setWorkspacePages(prev => ({ ...prev, [sourceWs!]: sourcePages }));

      // Find the page object
      const movedPage = (workspacePages[sourceWs!] || []).find(p => p.id === pageId);
      if (!movedPage) return;

      // Insert into target at the right position
      const clampedIdx = Math.min(targetIdx, targetPages.length);
      targetPages.splice(clampedIdx, 0, { ...movedPage, workspace: targetWs });
    } else {
      // Reorder within same workspace
      const currentIdx = targetPages.findIndex(p => p.id === pageId);
      if (currentIdx === -1) return;
      const [moved] = targetPages.splice(currentIdx, 1);
      const insertIdx = targetIdx > currentIdx ? targetIdx - 1 : targetIdx;
      targetPages.splice(Math.max(0, insertIdx), 0, moved);
    }

    // Optimistic update
    setWorkspacePages(prev => ({ ...prev, [targetWs]: targetPages }));

    // Persist to backend
    const newOrder = targetPages.map(p => p.id);
    try {
      await reorderPages(newOrder, isMoving ? targetWs : undefined);
      if (isMoving) {
        // Also persist remaining source order
        const remainingSource = (workspacePages[sourceWs!] || []).filter(p => p.id !== pageId);
        if (remainingSource.length > 0) {
          await reorderPages(remainingSource.map(p => p.id));
        }
      }
    } catch (err) {
      console.error("Reorder failed:", err);
    }
  }, [dragSourceWs, dropIndex, workspacePages]);

  // Workspace drag handlers
  const handleWsDragStart = useCallback((e: React.DragEvent, wsName: string) => {
    e.stopPropagation();
    setDragWsName(wsName);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("application/x-workspace", wsName);
  }, []);

  const handleWsDragEnd = useCallback(() => {
    setDragWsName(null);
    setDropWsIndex(null);
  }, []);

  const handleWsDragOver = useCallback((e: React.DragEvent, idx: number) => {
    if (!e.dataTransfer.types.includes("application/x-workspace")) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    const rect = e.currentTarget.getBoundingClientRect();
    const midY = rect.top + rect.height / 2;
    setDropWsIndex(e.clientY < midY ? idx : idx + 1);
  }, []);

  const handleWsDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    const wsName = e.dataTransfer.getData("application/x-workspace");
    if (!wsName || dropWsIndex === null) return;

    const currentIdx = workspaceMeta.findIndex(w => w.name === wsName);
    if (currentIdx === -1) return;

    // Compute new order
    const newMeta = [...workspaceMeta];
    const [moved] = newMeta.splice(currentIdx, 1);
    const insertIdx = dropWsIndex > currentIdx ? dropWsIndex - 1 : dropWsIndex;
    newMeta.splice(Math.max(0, insertIdx), 0, moved);

    // Reset drag state
    setDragWsName(null);
    setDropWsIndex(null);

    // Optimistic update
    setWorkspaceMeta(newMeta);

    // Persist to backend
    try {
      await reorderWorkspaces(newMeta.map(w => w.name));
    } catch (err) {
      console.error("Workspace reorder failed:", err);
    }
  }, [dropWsIndex, workspaceMeta]);

  // Load workspace metadata
  useEffect(() => {
    getWorkspaceMeta()
      .then(setWorkspaceMeta)
      .catch(() => setWorkspaceMeta([]));
  }, [refreshKey]);

  // Load pages grouped by workspace
  useEffect(() => {
    if (workspaceMeta.length === 0) return;

    const promises = workspaceMeta.map((ws) =>
      listPages(ws.name)
        .then((res) => ({
          name: ws.name,
          pages: res.pages.filter((p: Page) => !p.is_trashed),
        }))
        .catch(() => ({ name: ws.name, pages: [] as Page[] })),
    );

    Promise.all(promises).then((results) => {
      const map: Record<string, Page[]> = {};
      const allFavs: Page[] = [];
      for (const r of results) {
        map[r.name] = r.pages;
        for (const p of r.pages) {
          if (p.is_favorite) allFavs.push(p);
        }
      }
      setWorkspacePages(map);
      setFavorites(allFavs);
    });
  }, [workspaceMeta, refreshKey]);

  useEffect(() => {
    getRecentPages()
      .then(setRecentPages)
      .catch(() => setRecentPages([]));
  }, [refreshKey]);

  useEffect(() => {
    listTables()
      .then(setTables)
      .catch(() => setTables([]));
  }, [refreshKey]);

  const toggleSection = (key: string) => {
    setSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleQuickCreate = async () => {
    try {
      const page = await createPage({ title: "Untitled", workspace: activeWorkspace });
      onOpenPage(page);
    } catch (err) {
      console.error("Quick create failed:", err);
    }
  };

  const handleTrashPage = async (page: Page, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await updatePage(page.id, { is_trashed: true });
      // Refresh workspace pages
      const ws = page.workspace;
      const res = await listPages(ws);
      setWorkspacePages((prev) => ({
        ...prev,
        [ws]: res.pages.filter((p: Page) => !p.is_trashed),
      }));
    } catch (err) {
      console.error("Trash failed:", err);
    }
  };

  const handleExportMd = (page: Page, e: React.MouseEvent) => {
    e.stopPropagation();
    exportPageMd(page);
  };

  const handleExportPdf = (pageId: string, title: string, e: React.MouseEvent) => {
    e.stopPropagation();
    exportPagePdf(pageId, title).catch((err) =>
      console.error("PDF export failed:", err),
    );
  };

  const navItem = (
    label: string,
    icon: React.ReactNode,
    view: View,
    onClick?: () => void,
  ) => {
    const isActive = currentView === view;
    return (
      <button
        onClick={onClick ?? (() => onNavigate(view))}
        className={`w-full flex items-center gap-2.5 px-3 py-1.5 rounded text-[13px] transition-colors ${
          isActive
            ? "bg-sidebar-active text-white border-l-2 border-accent"
            : "text-sidebar-muted hover:bg-sidebar-hover hover:text-gray-200 border-l-2 border-transparent"
        }`}
      >
        <span className="shrink-0 opacity-70">{icon}</span>
        {!collapsed && <span className="truncate">{label}</span>}
      </button>
    );
  };

  const sectionHeader = (
    label: string,
    key: string,
    count?: number,
    action?: React.ReactNode,
  ) => (
    <div className="w-full flex items-center justify-between px-3 py-1 mt-4 mb-0.5 group">
      <button
        onClick={() => toggleSection(key)}
        className="flex items-center gap-1"
      >
        <span className="text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted/60 group-hover:text-sidebar-muted transition-colors">
          {label}
          {count !== undefined && count > 0 && (
            <span className="ml-1.5 text-[10px] font-normal opacity-50">
              {count}
            </span>
          )}
        </span>
        <span className="text-[9px] text-sidebar-muted/40 group-hover:text-sidebar-muted/60 transition-colors ml-0.5">
          {sections[key] ? "\u25B4" : "\u25BE"}
        </span>
      </button>
      {action && (
        <span className="opacity-0 group-hover:opacity-100 transition-opacity">
          {action}
        </span>
      )}
    </div>
  );

  const pageItemWithActions = (page: Page, wsName: string, idx: number) => {
    const isDragging = dragPageId === page.id;
    const showDropAbove = dropTargetWs === wsName && dropIndex === idx && dragPageId !== null && dragPageId !== page.id;

    return (
      <div key={page.id}>
        {/* Drop indicator line above */}
        {showDropAbove && (
          <div className="h-0.5 mx-3 bg-accent rounded-full" />
        )}
        <div
          draggable
          onDragStart={(e) => handleDragStart(e, page)}
          onDragEnd={handleDragEnd}
          onDragOver={(e) => handleDragOverPage(e, wsName, idx)}
          onDrop={(e) => handleDrop(e, wsName)}
          className={`w-full flex items-center gap-2 px-3 py-1 rounded text-[13px] text-sidebar-muted hover:bg-sidebar-hover hover:text-gray-200 transition-colors group/page cursor-grab active:cursor-grabbing ${
            isDragging ? "opacity-40" : ""
          }`}
          onClick={() => onOpenPage(page)}
        >
          <span className="shrink-0 opacity-30 cursor-grab">
            <Fa icon={faGripVertical} size="xs" />
          </span>
          <span className="shrink-0 opacity-50"><Fa icon={faFile} size="xs" /></span>
          <span className="truncate flex-1">{page.title}</span>
          {/* Hover-reveal action icons */}
          <span className="hidden group-hover/page:flex items-center gap-0.5 shrink-0">
            <button
              onClick={(e) => handleExportMd(page, e)}
              className="w-5 h-5 flex items-center justify-center rounded text-sidebar-muted/50 hover:text-accent-light hover:bg-sidebar-active transition-colors"
              title="Export MD"
            >
              <Fa icon={faDownload} size="xs" />
            </button>
            <button
              onClick={(e) => handleExportPdf(page.id, page.title, e)}
              className="w-5 h-5 flex items-center justify-center rounded text-sidebar-muted/50 hover:text-accent-light hover:bg-sidebar-active transition-colors"
              title="Export PDF"
            >
              <Fa icon={faFilePdf} size="xs" />
            </button>
            <button
              onClick={(e) => handleTrashPage(page, e)}
              className="w-5 h-5 flex items-center justify-center rounded text-sidebar-muted/50 hover:text-red-400 hover:bg-sidebar-active transition-colors"
              title="Delete"
            >
              <Fa icon={faTrashCan} size="xs" />
            </button>
          </span>
        </div>
      </div>
    );
  };

  if (collapsed) {
    return (
      <div className="w-11 bg-sidebar flex flex-col items-center py-3 gap-1.5 border-r border-sidebar-border shrink-0">
        <button
          onClick={onToggle}
          className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors mb-2"
          title="Expand sidebar"
        >
          <Fa icon={faChevronRight} size="xs" />
        </button>
        <button onClick={onOpenSearch} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Search">
          <Fa icon={faMagnifyingGlass} size="xs" />
        </button>
        <button onClick={() => onNavigate("home")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Home">
          <Fa icon={faHouse} size="xs" />
        </button>
        <button onClick={() => onNavigate("pages")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Pages">
          <Fa icon={faFile} size="xs" />
        </button>
        <button onClick={() => onNavigate("tables")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Tables">
          <Fa icon={faTable} size="xs" />
        </button>
        <button onClick={() => onNavigate("graph")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Graph">
          <Fa icon={faDiagramProject} size="xs" />
        </button>
        <button onClick={() => onNavigate("ai-chat")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="AI Chat">
          <Fa icon={faComments} size="xs" />
        </button>
        <button onClick={() => onNavigate("engines")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Engines">
          <Fa icon={faGear} size="xs" />
        </button>
      </div>
    );
  }

  return (
    <div
      className="bg-sidebar flex flex-col border-r border-sidebar-border shrink-0 h-full relative"
      style={{ width: SIDEBAR_WIDTH }}
    >

      {/* Header */}
      <div className="flex items-center justify-between px-3 pt-3 pb-1">
        <span className="text-sm font-semibold text-white tracking-tight">
          Katja
        </span>
        <button
          onClick={onToggle}
          className="w-6 h-6 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors"
          title="Collapse sidebar"
        >
          <Fa icon={faChevronLeft} size="xs" />
        </button>
      </div>

      {/* Search */}
      <div className="px-2 py-2">
        <button
          onClick={onOpenSearch}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-[13px] text-sidebar-muted hover:bg-sidebar-hover transition-colors"
        >
          <Fa icon={faMagnifyingGlass} size="xs" />
          <span className="flex-1 text-left">Search</span>
          <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-sidebar-hover text-sidebar-muted/60 font-mono">
            {"\u2318"}K
          </kbd>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto sidebar-scroll px-2 pb-3">
        <div className="space-y-0.5">
          {navItem("Home", <Fa icon={faHouse} size="xs" />, "home")}
          {navItem("All Pages", <Fa icon={faFile} size="xs" />, "pages")}
          {navItem("Graph View", <Fa icon={faDiagramProject} size="xs" />, "graph")}
          {navItem("AI Chat", <Fa icon={faComments} size="xs" />, "ai-chat")}
          {navItem("Engines", <Fa icon={faGear} size="xs" />, "engines")}
          {navItem("Trash", <Fa icon={faTrashCan} size="xs" />, "trash")}
        </div>

        {/* Favorites */}
        {favorites.length > 0 && (
          <>
            {sectionHeader("Favorites", "favorites", favorites.length)}
            {sections.favorites && (
              <div className="space-y-0.5">
                {favorites.map((page) => (
                  <button
                    key={page.id}
                    onClick={() => onOpenPage(page)}
                    className="w-full flex items-center gap-2 px-3 py-1 rounded text-[13px] text-sidebar-muted hover:bg-sidebar-hover hover:text-gray-200 transition-colors"
                  >
                    <span className="shrink-0 opacity-50"><Fa icon={faStar} size="xs" /></span>
                    <span className="truncate">{page.title}</span>
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        {/* Workspace-grouped pages */}
        {workspaceMeta.map((ws, wsIdx) => {
          const wsPages = workspacePages[ws.name] || [];
          const wsKey = `ws_${ws.name}`;
          const isOpen = sections[wsKey] !== false;
          const pageSlice = wsPages.slice(0, 10);
          const moreCount = wsPages.length - 10;

          const isDropTarget = dropTargetWs === ws.name && dragPageId !== null;
          const showDropAtEnd = isDropTarget && dropIndex === pageSlice.length && dragSourceWs !== null;

          const isDraggingWs = dragWsName === ws.name;
          const showWsDropAbove = dropWsIndex === wsIdx && dragWsName !== null && dragWsName !== ws.name;

          return (
            <div key={ws.name}>
              {/* Workspace drop indicator line */}
              {showWsDropAbove && (
                <div className="h-0.5 mx-3 mt-2 bg-accent rounded-full" />
              )}
              <div
                draggable
                onDragStart={(e) => handleWsDragStart(e, ws.name)}
                onDragEnd={handleWsDragEnd}
                onDragOver={(e) => {
                  handleWsDragOver(e, wsIdx);
                  handleDragOverWsHeader(e, ws.name);
                }}
                onDragLeave={handleDragLeave}
                onDrop={(e) => {
                  if (e.dataTransfer.types.includes("application/x-workspace")) {
                    handleWsDrop(e);
                  } else {
                    handleDrop(e, ws.name);
                  }
                }}
                className={`w-full flex items-center justify-between px-3 py-1 mt-3 mb-0.5 group rounded transition-colors cursor-grab active:cursor-grabbing ${
                  isDropTarget && dragSourceWs !== ws.name ? "bg-accent/10 ring-1 ring-accent/30" : ""
                } ${isDraggingWs ? "opacity-40" : ""}`}
              >
                <button
                  onClick={() => toggleSection(wsKey)}
                  className="flex items-center gap-1.5 min-w-0"
                >
                  <span className="shrink-0 opacity-30 cursor-grab group-hover:opacity-60 transition-opacity">
                    <Fa icon={faGripVertical} size="xs" />
                  </span>
                  <span className="shrink-0 opacity-70"><WorkspaceIcon icon={ws.icon} size="xs" /></span>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted/60 group-hover:text-sidebar-muted transition-colors truncate">
                    {ws.name}
                    <span className="ml-1.5 text-[10px] font-normal opacity-50">
                      {ws.page_count}
                    </span>
                  </span>
                  <span className="text-[9px] text-sidebar-muted/40 group-hover:text-sidebar-muted/60 transition-colors ml-0.5">
                    {isOpen ? "\u25B4" : "\u25BE"}
                  </span>
                </button>
                <button
                  onClick={handleQuickCreate}
                  className="w-5 h-5 flex items-center justify-center rounded text-sidebar-muted/40 hover:text-white hover:bg-sidebar-hover transition-colors opacity-0 group-hover:opacity-100"
                  title="New page"
                >
                  <Fa icon={faPlus} size="xs" />
                </button>
              </div>
              {isOpen && (
                <div>
                  {pageSlice.map((page, idx) => pageItemWithActions(page, ws.name, idx))}
                  {/* Drop indicator at end of list */}
                  {showDropAtEnd && (
                    <div className="h-0.5 mx-3 bg-accent rounded-full" />
                  )}
                  {moreCount > 0 && (
                    <button
                      onClick={() => {
                        onSetWorkspace(ws.name);
                        onNavigate("pages");
                      }}
                      className="w-full px-3 py-1 text-[11px] text-sidebar-muted/40 hover:text-sidebar-muted transition-colors text-left"
                    >
                      +{moreCount} more
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
        {/* Workspace drop indicator at end */}
        {dropWsIndex === workspaceMeta.length && dragWsName !== null && (
          <div className="h-0.5 mx-3 mt-2 bg-accent rounded-full" />
        )}

        {/* Tables */}
        {sectionHeader("Tables", "tables", tables.length)}
        {sections.tables && (
          <div className="space-y-0.5">
            {tables.map((table) => (
              <button
                key={table.name}
                onClick={() => onOpenTable(table.name)}
                className="w-full flex items-center gap-2 px-3 py-1 rounded text-[13px] text-sidebar-muted hover:bg-sidebar-hover hover:text-gray-200 transition-colors"
              >
                <span className="shrink-0 opacity-50"><Fa icon={faTable} size="xs" /></span>
                <span className="truncate">{table.name}</span>
                <span className="ml-auto text-[10px] opacity-40">
                  {table.row_count}
                </span>
              </button>
            ))}
            <button
              onClick={() => onNavigate("tables")}
              className="w-full flex items-center gap-2 px-3 py-1 rounded text-[13px] text-sidebar-muted/40 hover:bg-sidebar-hover hover:text-gray-300 transition-colors"
            >
              <span className="shrink-0"><Fa icon={faPlus} size="xs" /></span>
              <span>New Table</span>
            </button>
          </div>
        )}

        {/* Recent */}
        {sectionHeader("Recent", "recent", recentPages.length)}
        {sections.recent && (
          <div className="space-y-0.5">
            {recentPages.slice(0, 8).map((page) => (
              <button
                key={page.id}
                onClick={() => onOpenPage(page)}
                className="w-full flex items-center gap-2 px-3 py-1 rounded text-[13px] text-sidebar-muted hover:bg-sidebar-hover hover:text-gray-200 transition-colors"
              >
                <span className="shrink-0 opacity-50"><Fa icon={faFile} size="xs" /></span>
                <span className="truncate">{page.title}</span>
              </button>
            ))}
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-sidebar-border">
        <div className="flex items-center gap-2 text-[11px] text-sidebar-muted/40">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
          <span>Local</span>
        </div>
      </div>
    </div>
  );
}
