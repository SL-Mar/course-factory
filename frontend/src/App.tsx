import { useState, useEffect, useCallback } from "react";
import { AppShell } from "./components/layout/AppShell";
import { PageEditor } from "./components/editor/PageEditor";
import { PageList } from "./components/pages/PageList";
import { TableView } from "./components/tables/TableView";
import { GraphView } from "./components/graph/GraphView";
import { ChatPanel } from "./components/ai/ChatPanel";
import { SearchModal } from "./components/search/SearchModal";
import { EnginePanel } from "./components/engines/EnginePanel";
import { HomeView } from "./components/home/HomeView";
import { useApp } from "./hooks/useApp";
import type { Page, View } from "./types";
import { searchPages } from "./api/pages";

export default function App() {
  const {
    state,
    navigate,
    openPage,
    closePage,
    openTable,
    setWorkspace,
    toggleSidebar,
    openSearch,
    closeSearch,
  } = useApp();

  // Global Cmd+K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (state.searchOpen) {
          closeSearch();
        } else {
          openSearch();
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [state.searchOpen, openSearch, closeSearch]);

  // Handle wiki-link clicks: search for the page by title and open it
  const handleWikiLinkClick = useCallback(
    async (target: string) => {
      try {
        const results = await searchPages(target);
        if (results.length > 0) {
          openPage(results[0].page);
        }
      } catch {
        // Fallback: ignore if search fails
      }
    },
    [openPage],
  );

  // Handle graph node click
  const handleGraphNodeClick = useCallback(
    async (pageId: string, _title: string) => {
      try {
        const results = await searchPages(pageId);
        if (results.length > 0) {
          openPage(results[0].page);
        }
      } catch {
        // Ignore
      }
    },
    [openPage],
  );

  const [refreshKey, setRefreshKey] = useState(0);
  const triggerRefresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  const handlePageUpdated = useCallback((_page: Page) => {
    triggerRefresh();
  }, [triggerRefresh]);

  const handleSearchNavigate = useCallback(
    (view: string) => {
      navigate(view as View);
    },
    [navigate],
  );

  const handleSelectWorkspace = useCallback((workspace: string) => {
    setWorkspace(workspace);
  }, [setWorkspace]);

  const renderContent = () => {
    switch (state.view) {
      case "home":
        return (
          <HomeView
            onSelectWorkspace={handleSelectWorkspace}
            onNavigate={navigate}
            onWorkspacesChanged={triggerRefresh}
          />
        );

      case "pages":
        return (
          <PageList
            workspace={state.activeWorkspace}
            onOpenPage={openPage}
          />
        );

      case "page-editor":
        if (!state.activePage) {
          return (
            <PageList
              workspace={state.activeWorkspace}
              onOpenPage={openPage}
            />
          );
        }
        return (
          <PageEditor
            page={state.activePage}
            onClose={() => { closePage(); triggerRefresh(); }}
            onPageUpdated={handlePageUpdated}
            onWikiLinkClick={handleWikiLinkClick}
          />
        );

      case "tables":
        return <TableView tableName={null} onOpenTable={openTable} />;

      case "table-view":
        return (
          <TableView
            tableName={state.activeTable}
            onOpenTable={openTable}
          />
        );

      case "graph":
        return (
          <GraphView
            focusPageId={state.activePage?.id}
            initialWorkspace={state.activeWorkspace}
            onOpenPage={handleGraphNodeClick}
          />
        );

      case "ai-chat":
        return (
          <ChatPanel
            activePageId={state.activePage?.id}
            activePageContent={state.activePage?.content}
          />
        );

      case "engines":
        return <EnginePanel />;

      case "trash":
        return (
          <PageList
            workspace={state.activeWorkspace}
            onOpenPage={openPage}
            showTrashed={true}
          />
        );

      default:
        return (
          <PageList
            workspace={state.activeWorkspace}
            onOpenPage={openPage}
          />
        );
    }
  };

  return (
    <>
      <AppShell
        currentView={state.view}
        activeWorkspace={state.activeWorkspace}
        sidebarCollapsed={state.sidebarCollapsed}
        refreshKey={refreshKey}
        onNavigate={navigate}
        onOpenPage={openPage}
        onOpenTable={openTable}
        onSetWorkspace={setWorkspace}
        onToggleSidebar={toggleSidebar}
        onOpenSearch={openSearch}
      >
        {renderContent()}
      </AppShell>

      <SearchModal
        isOpen={state.searchOpen}
        onClose={closeSearch}
        onOpenPage={openPage}
        onNavigate={handleSearchNavigate}
      />
    </>
  );
}
