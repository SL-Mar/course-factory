import type { ReactNode } from "react";
import type { AppView } from "../../types/app";
import { cn } from "../../utils/cn";

interface AppShellProps {
  currentView: AppView;
  onNavigate: (view: AppView) => void;
  children: ReactNode;
}

export function AppShell({ currentView, onNavigate, children }: AppShellProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-surface-border px-6 py-3">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <button
            onClick={() => onNavigate("dashboard")}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
              CF
            </div>
            <span className="text-sm font-semibold text-gray-300">
              Course Factory
            </span>
          </button>
          <nav className="flex items-center gap-1">
            <NavButton
              active={currentView === "dashboard"}
              onClick={() => onNavigate("dashboard")}
            >
              Courses
            </NavButton>
            <NavButton
              active={currentView === "setup"}
              onClick={() => onNavigate("setup")}
            >
              Settings
            </NavButton>
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}

function NavButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-md px-3 py-1.5 text-sm transition-colors",
        active
          ? "bg-surface-card text-gray-100"
          : "text-gray-500 hover:text-gray-300",
      )}
    >
      {children}
    </button>
  );
}
