import { useState, useEffect, useCallback, useRef } from "react";
import type { Page, PageUpdate } from "../../types";
import { getPage, updatePage, deletePage } from "../../api/pages";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface PageEditorProps {
  page: Page;
  onClose: () => void;
  onPageUpdated: (page: Page) => void;
  onWikiLinkClick: (target: string) => void;
}

type EditorMode = "edit" | "preview";

export function PageEditor({
  page: initialPage,
  onClose,
  onPageUpdated,
  onWikiLinkClick,
}: PageEditorProps) {
  const [page, setPage] = useState<Page>(initialPage);
  const [title, setTitle] = useState(initialPage.title);
  const [content, setContent] = useState(initialPage.content);
  const [mode, setMode] = useState<EditorMode>("preview");
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [dirty, setDirty] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout>>();

  // Reload page data on mount
  useEffect(() => {
    getPage(initialPage.id)
      .then((fresh) => {
        setPage(fresh);
        setTitle(fresh.title);
        setContent(fresh.content);
      })
      .catch(() => {
        // Use initial data if fetch fails
      });
  }, [initialPage.id]);

  const save = useCallback(async () => {
    if (!dirty) return;
    setSaving(true);
    try {
      const update: PageUpdate = {};
      if (title !== page.title) update.title = title;
      if (content !== page.content) update.content = content;

      if (Object.keys(update).length > 0) {
        const updated = await updatePage(page.id, update);
        setPage(updated);
        onPageUpdated(updated);
        setLastSaved(new Date());
        setDirty(false);
      }
    } catch (err) {
      console.error("Save failed:", err);
    } finally {
      setSaving(false);
    }
  }, [title, content, page, dirty, onPageUpdated]);

  // Auto-save with debounce
  useEffect(() => {
    if (!dirty) return;
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      save();
    }, 1500);
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, [dirty, save]);

  // Cmd+S to save
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        save();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [save]);

  const handleTitleChange = (value: string) => {
    setTitle(value);
    setDirty(true);
  };

  const handleContentChange = (value: string) => {
    setContent(value);
    setDirty(true);
  };

  const toggleFavorite = async () => {
    try {
      const updated = await updatePage(page.id, {
        is_favorite: !page.is_favorite,
      });
      setPage(updated);
      onPageUpdated(updated);
    } catch (err) {
      console.error("Toggle favorite failed:", err);
    }
  };

  const moveToTrash = async () => {
    try {
      await updatePage(page.id, { is_trashed: true });
      onClose();
    } catch (err) {
      console.error("Trash failed:", err);
    }
  };

  const permanentDelete = async () => {
    if (!confirm("Permanently delete this page? This cannot be undone.")) {
      return;
    }
    try {
      await deletePage(page.id);
      onClose();
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleTabKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const textarea = textareaRef.current;
      if (!textarea) return;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newContent =
        content.substring(0, start) + "  " + content.substring(end);
      handleContentChange(newContent);
      requestAnimationFrame(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2;
      });
    }
  };

  return (
    <div className="h-full flex flex-col bg-content">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-content-border bg-content-secondary shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-content-tertiary transition-colors text-content-muted hover:text-content-text"
            title="Back"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M10 3l-5 5 5 5" />
            </svg>
          </button>
          <span className="text-xs text-content-faint">{page.workspace}</span>
          <span className="text-xs text-content-faint">/</span>
          <span className="text-xs font-medium text-content-text truncate max-w-[240px]">
            {title || "Untitled"}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Save status */}
          <div className="flex items-center gap-1.5 text-[11px] text-content-muted mr-2">
            {saving && (
              <>
                <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                <span>Saving...</span>
              </>
            )}
            {!saving && lastSaved && (
              <>
                <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                <span>Saved</span>
              </>
            )}
            {!saving && dirty && !lastSaved && (
              <>
                <div className="w-1.5 h-1.5 rounded-full bg-content-faint" />
                <span>Unsaved</span>
              </>
            )}
          </div>

          {/* Mode toggle */}
          <div className="flex items-center border border-content-border rounded overflow-hidden">
            <button
              onClick={() => setMode("edit")}
              className={`px-2.5 py-1 text-[11px] transition-colors ${
                mode === "edit"
                  ? "bg-accent text-white"
                  : "text-content-muted hover:text-content-text bg-content-secondary"
              }`}
            >
              Edit
            </button>
            <button
              onClick={() => setMode("preview")}
              className={`px-2.5 py-1 text-[11px] transition-colors ${
                mode === "preview"
                  ? "bg-accent text-white"
                  : "text-content-muted hover:text-content-text bg-content-secondary"
              }`}
            >
              Preview
            </button>
          </div>

          {/* Favorite */}
          <button
            onClick={toggleFavorite}
            className={`px-1.5 py-1 rounded text-xs hover:bg-content-tertiary transition-colors ${
              page.is_favorite ? "text-amber-500" : "text-content-muted"
            }`}
            title={page.is_favorite ? "Unfavorite" : "Favorite"}
          >
            {page.is_favorite ? "\u2605" : "\u2606"}
          </button>

          {/* Menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="px-1.5 py-1 rounded hover:bg-content-tertiary transition-colors text-content-muted text-xs"
            >
              {"\u22EF"}
            </button>
            {showMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowMenu(false)}
                />
                <div className="absolute right-0 top-full mt-1 w-44 bg-content-secondary border border-content-border rounded shadow-lg z-20 py-1">
                  <button
                    onClick={() => { setShowMenu(false); moveToTrash(); }}
                    className="w-full px-3 py-1.5 text-left text-xs text-content-muted hover:bg-content-tertiary transition-colors"
                  >
                    Move to Trash
                  </button>
                  <button
                    onClick={() => { setShowMenu(false); permanentDelete(); }}
                    className="w-full px-3 py-1.5 text-left text-xs text-red-400 hover:bg-content-tertiary transition-colors"
                  >
                    Delete Permanently
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Page body */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-12 py-8">
          {/* Title */}
          <input
            type="text"
            value={title}
            onChange={(e) => handleTitleChange(e.target.value)}
            placeholder="Untitled"
            className="w-full text-2xl font-bold text-content-text bg-transparent border-none outline-none placeholder-content-faint mb-1"
          />

          {/* Tags */}
          {page.tags.length > 0 && (
            <div className="flex gap-1.5 flex-wrap mb-4">
              {page.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 text-[11px] rounded bg-content-tertiary text-content-muted"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Divider */}
          <div className="border-t border-content-border mb-6" />

          {/* Content */}
          {mode === "edit" ? (
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => handleContentChange(e.target.value)}
              onKeyDown={handleTabKey}
              placeholder="Start writing... Use **bold**, *italic*, [[Wiki Links]], and Markdown."
              className="w-full min-h-[400px] pb-16 text-sm leading-relaxed text-content-text bg-transparent resize-none outline-none placeholder-content-faint font-mono"
              spellCheck={false}
              style={{ minHeight: "calc(100vh - 300px)" }}
            />
          ) : (
            <div className="pb-16">
              {content ? (
                <MarkdownRenderer
                  content={content}
                  onWikiLinkClick={onWikiLinkClick}
                />
              ) : (
                <p className="text-content-faint text-sm">
                  Empty page. Switch to Edit mode to start writing.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
