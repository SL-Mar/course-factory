import { useState, useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faXmark, faSearch, faFileLines } from "@fortawesome/free-solid-svg-icons";
import { listPages } from "../../api/pages";
import type { Page } from "../../types";

interface PagePickerModalProps {
  currentPageId: string;
  onInsert: (markdown: string) => void;
  onClose: () => void;
}

export function PagePickerModal({ currentPageId, onInsert, onClose }: PagePickerModalProps) {
  const [query, setQuery] = useState("");
  const [pages, setPages] = useState<Page[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listPages().then((res) => {
      setPages(res.pages.filter((p: Page) => p.id !== currentPageId));
    });
  }, [currentPageId]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const filtered = pages.filter((p) => {
    if (!query) return true;
    return p.title.toLowerCase().includes(query.toLowerCase());
  }).slice(0, 20);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleSelect = (page: Page) => {
    onInsert(`[[${page.title}]]`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        handleSelect(filtered[selectedIndex]);
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    }
  };

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/60" onClick={onClose} />
      <div className="fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[420px] bg-content-secondary border border-content-border rounded-lg shadow-2xl animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-content-border">
          <span className="text-sm font-medium text-content-text">Insert Page Link</span>
          <button onClick={onClose} className="text-content-muted hover:text-content-text">
            <FontAwesomeIcon icon={faXmark} />
          </button>
        </div>

        {/* Search */}
        <div className="px-4 py-2 border-b border-content-border">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-content-tertiary border border-content-border rounded">
            <FontAwesomeIcon icon={faSearch} className="text-content-faint text-xs" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search pages..."
              className="flex-1 text-xs bg-transparent text-content-text outline-none placeholder-content-faint"
            />
          </div>
        </div>

        {/* Results */}
        <div className="max-h-64 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="px-4 py-6 text-center text-xs text-content-muted">
              No pages found
            </div>
          ) : (
            filtered.map((page, idx) => (
              <button
                key={page.id}
                onClick={() => handleSelect(page)}
                className={`w-full flex items-center gap-3 px-4 py-2 text-left transition-colors ${
                  idx === selectedIndex
                    ? "bg-accent/15 text-accent-light"
                    : "text-content-text hover:bg-content-tertiary"
                }`}
              >
                <FontAwesomeIcon
                  icon={faFileLines}
                  className={`text-xs ${idx === selectedIndex ? "text-accent" : "text-content-muted"}`}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium truncate">{page.title}</div>
                  <div className="text-[10px] text-content-muted truncate">{page.workspace}</div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </>
  );
}
