import { useState, useEffect, useCallback } from "react";
import type { Page, PageCreate } from "../../types";
import { listPages, createPage, updatePage } from "../../api/pages";

interface PageListProps {
  workspace: string;
  onOpenPage: (page: Page) => void;
  showTrashed?: boolean;
}

type SortField = "title" | "updated_at" | "created_at" | "word_count";
type SortDir = "asc" | "desc";

export function PageList({
  workspace,
  onOpenPage,
  showTrashed = false,
}: PageListProps) {
  const [pages, setPages] = useState<Page[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState<SortField>("updated_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [filterTag, setFilterTag] = useState<string>("");

  const loadPages = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listPages(workspace, showTrashed);
      let filtered = showTrashed
        ? res.pages.filter((p) => p.is_trashed)
        : res.pages.filter((p) => !p.is_trashed);

      if (filterTag) {
        filtered = filtered.filter((p) =>
          p.tags.some((t) => t.toLowerCase().includes(filterTag.toLowerCase())),
        );
      }

      filtered.sort((a, b) => {
        let cmp: number;
        if (sortField === "title") {
          cmp = a.title.localeCompare(b.title);
        } else if (sortField === "word_count") {
          cmp = (a.word_count ?? 0) - (b.word_count ?? 0);
        } else {
          cmp =
            new Date(a[sortField]).getTime() -
            new Date(b[sortField]).getTime();
        }
        return sortDir === "asc" ? cmp : -cmp;
      });

      setPages(filtered);
    } catch {
      setPages([]);
    } finally {
      setLoading(false);
    }
  }, [workspace, showTrashed, sortField, sortDir, filterTag]);

  useEffect(() => {
    loadPages();
  }, [loadPages]);

  const handleQuickCreate = async () => {
    try {
      const data: PageCreate = { title: "Untitled", workspace };
      const page = await createPage(data);
      onOpenPage(page);
    } catch (err) {
      console.error("Create page failed:", err);
    }
  };

  const handleRestore = async (page: Page) => {
    try {
      await updatePage(page.id, { is_trashed: false });
      loadPages();
    } catch (err) {
      console.error("Restore failed:", err);
    }
  };

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir(field === "title" ? "asc" : "desc");
    }
  };

  const allTags = Array.from(new Set(pages.flatMap((p) => p.tags)));

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString();
  };

  const sortArrow = (field: SortField) => {
    if (sortField !== field) return null;
    return (
      <span className="ml-1 text-accent-light">
        {sortDir === "asc" ? "\u2191" : "\u2193"}
      </span>
    );
  };

  return (
    <div className="h-full flex flex-col bg-content">
      {/* Header */}
      <div className="px-6 pt-6 pb-3 border-b border-content-border">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-content-text">
              {showTrashed ? "Trash" : "Pages"}
            </h1>
            <p className="text-xs text-content-muted mt-0.5">
              {showTrashed
                ? `${pages.length} trashed`
                : `${pages.length} pages in ${workspace}`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {allTags.length > 0 && (
              <select
                value={filterTag}
                onChange={(e) => setFilterTag(e.target.value)}
                className="text-xs border border-content-border rounded px-2 py-1 text-content-text bg-content-secondary focus:outline-none focus:border-accent"
              >
                <option value="">All tags</option>
                {allTags.map((tag) => (
                  <option key={tag} value={tag}>{tag}</option>
                ))}
              </select>
            )}
            {!showTrashed && (
              <button
                onClick={handleQuickCreate}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-accent text-white text-xs font-medium rounded hover:bg-accent-hover transition-colors"
              >
                + New Page
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && pages.length === 0 && (
          <div className="text-center py-12">
            <p className="text-content-muted text-sm">
              {showTrashed ? "Trash is empty." : "No pages yet."}
            </p>
            {!showTrashed && (
              <button
                onClick={handleQuickCreate}
                className="mt-3 px-4 py-1.5 text-xs bg-accent text-white rounded hover:bg-accent-hover transition-colors"
              >
                Create your first page
              </button>
            )}
          </div>
        )}

        {!loading && pages.length > 0 && (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-content-border bg-content-secondary text-left">
                <th className="w-8 px-3 py-2" />
                <th className="px-3 py-2">
                  <button
                    onClick={() => toggleSort("title")}
                    className="text-[11px] font-semibold uppercase tracking-wider text-content-muted hover:text-content-text transition-colors"
                  >
                    Title{sortArrow("title")}
                  </button>
                </th>
                <th className="px-3 py-2 w-32">
                  <button
                    onClick={() => toggleSort("updated_at")}
                    className="text-[11px] font-semibold uppercase tracking-wider text-content-muted hover:text-content-text transition-colors"
                  >
                    Modified{sortArrow("updated_at")}
                  </button>
                </th>
                <th className="px-3 py-2 w-32">
                  <button
                    onClick={() => toggleSort("created_at")}
                    className="text-[11px] font-semibold uppercase tracking-wider text-content-muted hover:text-content-text transition-colors"
                  >
                    Created{sortArrow("created_at")}
                  </button>
                </th>
                <th className="px-3 py-2 w-16 text-right">
                  <button
                    onClick={() => toggleSort("word_count")}
                    className="text-[11px] font-semibold uppercase tracking-wider text-content-muted hover:text-content-text transition-colors"
                  >
                    Words{sortArrow("word_count")}
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {pages.map((page) => (
                <tr
                  key={page.id}
                  onClick={() =>
                    showTrashed ? handleRestore(page) : onOpenPage(page)
                  }
                  className="border-b border-content-border/50 hover:bg-content-secondary transition-colors cursor-pointer group"
                >
                  {/* Favorite indicator */}
                  <td className="px-3 py-2 text-center">
                    {page.is_favorite && (
                      <span className="text-amber-500 text-[10px]">{"\u2605"}</span>
                    )}
                  </td>
                  {/* Title + tags */}
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      <span className="text-content-text font-medium group-hover:text-accent-light transition-colors">
                        {page.title}
                      </span>
                      {page.tags.length > 0 && (
                        <div className="flex gap-1">
                          {page.tags.slice(0, 3).map((tag) => (
                            <span
                              key={tag}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-content-tertiary text-content-faint"
                            >
                              {tag}
                            </span>
                          ))}
                          {page.tags.length > 3 && (
                            <span className="text-[10px] text-content-faint">
                              +{page.tags.length - 3}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </td>
                  {/* Modified */}
                  <td className="px-3 py-2 text-xs text-content-muted">
                    {formatDate(page.updated_at)}
                  </td>
                  {/* Created */}
                  <td className="px-3 py-2 text-xs text-content-muted">
                    {formatDate(page.created_at)}
                  </td>
                  {/* Word count */}
                  <td className="px-3 py-2 text-xs text-content-muted text-right">
                    {page.word_count ?? 0}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
