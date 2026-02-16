import { useState, useEffect, useRef, useCallback } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
import type { SearchResult, Page } from "../../types";
import { searchPages, getRecentPages } from "../../api/pages";

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenPage: (page: Page) => void;
  onNavigate: (view: string) => void;
}

interface QuickAction {
  label: string;
  icon: string;
  action: string;
  shortcut?: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  { label: "All Pages", icon: "\uD83D\uDCC4", action: "pages", shortcut: "P" },
  { label: "Graph View", icon: "\u25C8", action: "graph", shortcut: "G" },
  { label: "AI Chat", icon: "\u269B", action: "ai-chat", shortcut: "C" },
  { label: "Tables", icon: "\uD83D\uDCCA", action: "tables", shortcut: "T" },
  { label: "Engines", icon: "\u2699", action: "engines", shortcut: "E" },
];

export function SearchModal({
  isOpen,
  onClose,
  onOpenPage,
  onNavigate,
}: SearchModalProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [recentPages, setRecentPages] = useState<Page[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchTimerRef = useRef<ReturnType<typeof setTimeout>>();

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setResults([]);
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);

      // Load recent pages
      getRecentPages()
        .then(setRecentPages)
        .catch(() => setRecentPages([]));
    }
  }, [isOpen]);

  // Global keyboard shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Parent component should call onOpenSearch
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const res = await searchPages(q);
      setResults(res);
      setSelectedIndex(0);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleInputChange = (value: string) => {
    setQuery(value);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => {
      doSearch(value);
    }, 250);
  };

  const totalItems = query.trim()
    ? results.length
    : recentPages.length + QUICK_ACTIONS.length;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, totalItems - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        handleSelect(selectedIndex);
        break;
      case "Escape":
        e.preventDefault();
        onClose();
        break;
    }
  };

  const handleSelect = (index: number) => {
    if (query.trim()) {
      // Search results
      const result = results[index];
      if (result) {
        onOpenPage(result.page);
        onClose();
      }
    } else {
      // Recent pages + quick actions
      if (index < recentPages.length) {
        const page = recentPages[index];
        onOpenPage(page);
        onClose();
      } else {
        const actionIndex = index - recentPages.length;
        const action = QUICK_ACTIONS[actionIndex];
        if (action) {
          onNavigate(action.action);
          onClose();
        }
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start justify-center pt-[15vh]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-xl bg-content-secondary rounded-xl shadow-2xl border border-content-border overflow-hidden animate-fade-in">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-content-border">
          <FontAwesomeIcon icon={faMagnifyingGlass} className="text-content-faint" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search pages, navigate..."
            className="flex-1 text-sm text-content-text bg-transparent border-none outline-none placeholder-content-muted"
          />
          {loading && (
            <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          )}
          <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-content-tertiary text-content-faint font-mono">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-[400px] overflow-y-auto">
          {query.trim() ? (
            // Search results
            <>
              {results.length === 0 && !loading && (
                <div className="px-4 py-8 text-center text-sm text-content-muted">
                  No results for "{query}"
                </div>
              )}
              {results.map((result, i) => (
                <button
                  key={result.page.id}
                  onClick={() => handleSelect(i)}
                  onMouseEnter={() => setSelectedIndex(i)}
                  className={`w-full flex items-start gap-3 px-4 py-3 text-left transition-colors ${
                    selectedIndex === i
                      ? "bg-content-tertiary"
                      : "hover:bg-content-tertiary"
                  }`}
                >
                  <span className="text-sm shrink-0 mt-0.5">
                    {result.page.icon || "\uD83D\uDCC4"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-content-text truncate">
                      {result.page.title}
                    </div>
                    {result.snippet && (
                      <div className="text-xs text-content-muted mt-0.5 line-clamp-2">
                        {result.snippet}
                      </div>
                    )}
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-content-muted">
                        {result.page.workspace}
                      </span>
                      <span className="text-[10px] text-content-faint">
                        Score: {(result.score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </>
          ) : (
            // Default: recent pages + quick actions
            <>
              {recentPages.length > 0 && (
                <>
                  <div className="px-4 py-2 text-[11px] font-semibold text-content-muted uppercase tracking-wider">
                    Recent Pages
                  </div>
                  {recentPages.slice(0, 5).map((page, i) => (
                    <button
                      key={page.id}
                      onClick={() => handleSelect(i)}
                      onMouseEnter={() => setSelectedIndex(i)}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                        selectedIndex === i
                          ? "bg-content-tertiary"
                          : "hover:bg-content-tertiary"
                      }`}
                    >
                      <span className="text-sm">
                        {page.icon || "\uD83D\uDCC4"}
                      </span>
                      <span className="text-sm text-content-text truncate flex-1">
                        {page.title}
                      </span>
                      <span className="text-[10px] text-content-muted">
                        {page.workspace}
                      </span>
                    </button>
                  ))}
                </>
              )}

              <div className="px-4 py-2 text-[11px] font-semibold text-content-muted uppercase tracking-wider border-t border-content-border mt-1 pt-2">
                Quick Actions
              </div>
              {QUICK_ACTIONS.map((action, i) => {
                const idx = recentPages.length + i;
                return (
                  <button
                    key={action.action}
                    onClick={() => handleSelect(idx)}
                    onMouseEnter={() => setSelectedIndex(idx)}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                      selectedIndex === idx
                        ? "bg-content-tertiary"
                        : "hover:bg-content-tertiary"
                    }`}
                  >
                    <span className="text-sm w-5 text-center">
                      {action.icon}
                    </span>
                    <span className="text-sm text-content-text flex-1">
                      {action.label}
                    </span>
                    {action.shortcut && (
                      <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-content-tertiary text-content-faint font-mono">
                        {action.shortcut}
                      </kbd>
                    )}
                  </button>
                );
              })}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-content-border bg-content-tertiary flex items-center gap-4 text-[10px] text-content-faint">
          <span>
            <kbd className="font-mono">{"\u2191\u2193"}</kbd> navigate
          </span>
          <span>
            <kbd className="font-mono">{"\u23CE"}</kbd> open
          </span>
          <span>
            <kbd className="font-mono">esc</kbd> close
          </span>
        </div>
      </div>
    </div>
  );
}
