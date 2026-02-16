import { useState, useEffect } from "react";
import type { View, Page, TableDef } from "../../types";
import { getRecentPages, getWorkspaces, listPages, createPage } from "../../api/pages";
import { listTables } from "../../api/tables";

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
  workspaces: boolean;
  favorites: boolean;
  pages: boolean;
  tables: boolean;
  recent: boolean;
}

/* ── Small inline SVG icons ── */

const IconChevronRight = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M6 3l5 5-5 5" />
  </svg>
);
const IconChevronLeft = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M10 3l-5 5 5 5" />
  </svg>
);
const IconSearch = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="7" cy="7" r="4.5" />
    <path d="M10.5 10.5L14 14" />
  </svg>
);
const IconFile = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M4 2h5l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z" />
    <path d="M9 2v4h4" />
  </svg>
);
const IconGraph = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="4" cy="4" r="2" />
    <circle cx="12" cy="4" r="2" />
    <circle cx="8" cy="12" r="2" />
    <path d="M5.5 5.5L7 10.5M10.5 5.5L9 10.5" />
  </svg>
);
const IconChat = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M2 3h12v8H5l-3 3V3z" strokeLinejoin="round" />
  </svg>
);
const IconGear = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="8" cy="8" r="2.5" />
    <path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.1 3.1l1.4 1.4M11.5 11.5l1.4 1.4M3.1 12.9l1.4-1.4M11.5 4.5l1.4-1.4" />
  </svg>
);
const IconTrash = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M3 4h10l-1 10H4L3 4zM6 4V2.5h4V4M2 4h12" />
  </svg>
);
const IconTable = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <rect x="2" y="2" width="12" height="12" rx="1" />
    <path d="M2 6h12M2 10h12M6 2v12" />
  </svg>
);
const IconPlus = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M6 2v8M2 6h8" />
  </svg>
);
const IconStar = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M8 2l1.8 3.6L14 6.2l-3 2.9.7 4.1L8 11.2 4.3 13.2l.7-4.1-3-2.9 4.2-.6L8 2z" />
  </svg>
);

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
  const [workspaces, setWorkspaces] = useState<string[]>([]);
  const [pages, setPages] = useState<Page[]>([]);
  const [favorites, setFavorites] = useState<Page[]>([]);
  const [recentPages, setRecentPages] = useState<Page[]>([]);
  const [tables, setTables] = useState<TableDef[]>([]);
  const [sections, setSections] = useState<SectionState>({
    workspaces: true,
    favorites: true,
    pages: true,
    tables: true,
    recent: false,
  });

  useEffect(() => {
    getWorkspaces()
      .then(setWorkspaces)
      .catch(() => setWorkspaces(["default"]));
  }, []);

  useEffect(() => {
    listPages(activeWorkspace)
      .then((res) => {
        setPages(res.pages.filter((p) => !p.is_trashed));
        setFavorites(res.pages.filter((p) => p.is_favorite && !p.is_trashed));
      })
      .catch(() => {
        setPages([]);
        setFavorites([]);
      });
  }, [activeWorkspace, refreshKey]);

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

  const toggleSection = (key: keyof SectionState) => {
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
    key: keyof SectionState,
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

  const pageItem = (page: Page) => (
    <button
      key={page.id}
      onClick={() => onOpenPage(page)}
      className="w-full flex items-center gap-2 px-3 py-1 rounded text-[13px] text-sidebar-muted hover:bg-sidebar-hover hover:text-gray-200 transition-colors"
    >
      <span className="shrink-0 opacity-50"><IconFile /></span>
      <span className="truncate">{page.title}</span>
    </button>
  );

  if (collapsed) {
    return (
      <div className="w-11 bg-sidebar flex flex-col items-center py-3 gap-1.5 border-r border-sidebar-border shrink-0">
        <button
          onClick={onToggle}
          className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors mb-2"
          title="Expand sidebar"
        >
          <IconChevronRight />
        </button>
        <button onClick={onOpenSearch} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Search">
          <IconSearch />
        </button>
        <button onClick={() => onNavigate("pages")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Pages">
          <IconFile />
        </button>
        <button onClick={() => onNavigate("tables")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Tables">
          <IconTable />
        </button>
        <button onClick={() => onNavigate("graph")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Graph">
          <IconGraph />
        </button>
        <button onClick={() => onNavigate("ai-chat")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="AI Chat">
          <IconChat />
        </button>
        <button onClick={() => onNavigate("engines")} className="w-7 h-7 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors" title="Engines">
          <IconGear />
        </button>
      </div>
    );
  }

  return (
    <div className="w-56 bg-sidebar flex flex-col border-r border-sidebar-border shrink-0 h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 pt-3 pb-1">
        <span className="text-sm font-semibold text-white tracking-tight">
          LocalNotion
        </span>
        <button
          onClick={onToggle}
          className="w-6 h-6 flex items-center justify-center rounded text-sidebar-muted hover:bg-sidebar-hover hover:text-white transition-colors"
          title="Collapse sidebar"
        >
          <IconChevronLeft />
        </button>
      </div>

      {/* Search */}
      <div className="px-2 py-2">
        <button
          onClick={onOpenSearch}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-[13px] text-sidebar-muted hover:bg-sidebar-hover transition-colors"
        >
          <IconSearch />
          <span className="flex-1 text-left">Search</span>
          <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-sidebar-hover text-sidebar-muted/60 font-mono">
            {"\u2318"}K
          </kbd>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto sidebar-scroll px-2 pb-3">
        <div className="space-y-0.5">
          {navItem("All Pages", <IconFile />, "pages")}
          {navItem("Graph View", <IconGraph />, "graph")}
          {navItem("AI Chat", <IconChat />, "ai-chat")}
          {navItem("Engines", <IconGear />, "engines")}
          {navItem("Trash", <IconTrash />, "trash")}
        </div>

        {/* Workspaces */}
        {workspaces.length > 0 && (
          <>
            {sectionHeader("Workspaces", "workspaces")}
            {sections.workspaces && (
              <div className="space-y-0.5">
                {workspaces.map((ws) => (
                  <button
                    key={ws}
                    onClick={() => onSetWorkspace(ws)}
                    className={`w-full flex items-center gap-2 px-3 py-1 rounded text-[13px] transition-colors ${
                      activeWorkspace === ws
                        ? "bg-sidebar-active text-white"
                        : "text-sidebar-muted hover:bg-sidebar-hover hover:text-gray-200"
                    }`}
                  >
                    <span className="text-[10px] opacity-50">
                      {activeWorkspace === ws ? "\u25BC" : "\u25B6"}
                    </span>
                    <span className="truncate capitalize">{ws}</span>
                  </button>
                ))}
              </div>
            )}
          </>
        )}

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
                    <span className="shrink-0 opacity-50"><IconStar /></span>
                    <span className="truncate">{page.title}</span>
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        {/* Pages */}
        {sectionHeader("Pages", "pages", pages.length,
          <button
            onClick={handleQuickCreate}
            className="w-5 h-5 flex items-center justify-center rounded text-sidebar-muted/40 hover:text-white hover:bg-sidebar-hover transition-colors"
            title="New page"
          >
            <IconPlus />
          </button>
        )}
        {sections.pages && (
          <div className="space-y-0.5">
            {pages.slice(0, 20).map((page) => pageItem(page))}
            {pages.length > 20 && (
              <div className="px-3 py-1 text-[11px] text-sidebar-muted/40">
                +{pages.length - 20} more
              </div>
            )}
          </div>
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
                <span className="shrink-0 opacity-50"><IconTable /></span>
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
              <span className="shrink-0"><IconPlus /></span>
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
                <span className="shrink-0 opacity-50"><IconFile /></span>
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
