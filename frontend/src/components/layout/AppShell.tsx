import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import type { View, Page } from "../../types";

interface AppShellProps {
  currentView: View;
  activeWorkspace: string;
  sidebarCollapsed: boolean;
  refreshKey: number;
  onNavigate: (view: View) => void;
  onOpenPage: (page: Page) => void;
  onOpenTable: (name: string) => void;
  onSetWorkspace: (workspace: string) => void;
  onToggleSidebar: () => void;
  onOpenSearch: () => void;
  children: ReactNode;
}

export function AppShell({
  currentView,
  activeWorkspace,
  sidebarCollapsed,
  refreshKey,
  onNavigate,
  onOpenPage,
  onOpenTable,
  onSetWorkspace,
  onToggleSidebar,
  onOpenSearch,
  children,
}: AppShellProps) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        currentView={currentView}
        activeWorkspace={activeWorkspace}
        collapsed={sidebarCollapsed}
        refreshKey={refreshKey}
        onNavigate={onNavigate}
        onOpenPage={onOpenPage}
        onOpenTable={onOpenTable}
        onSetWorkspace={onSetWorkspace}
        onToggle={onToggleSidebar}
        onOpenSearch={onOpenSearch}
      />
      <main className="flex-1 overflow-hidden bg-content">{children}</main>
    </div>
  );
}
