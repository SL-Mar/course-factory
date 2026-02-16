import { apiFetch } from "./client";
import type {
  Page,
  PageCreate,
  PageUpdate,
  PageListResponse,
  SearchResult,
  WorkspaceMeta,
} from "../types";

export async function listPages(
  workspace?: string,
  include_trashed = false,
): Promise<PageListResponse> {
  const params = new URLSearchParams();
  if (workspace) params.set("workspace", workspace);
  if (include_trashed) params.set("include_trashed", "true");
  params.set("limit", "1000");
  const qs = params.toString();
  return apiFetch<PageListResponse>(`/pages${qs ? `?${qs}` : ""}`);
}

export async function getPage(id: string): Promise<Page> {
  return apiFetch<Page>(`/pages/${id}`);
}

export async function createPage(data: PageCreate): Promise<Page> {
  return apiFetch<Page>("/pages", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updatePage(
  id: string,
  data: PageUpdate,
): Promise<Page> {
  return apiFetch<Page>(`/pages/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deletePage(id: string): Promise<void> {
  await apiFetch<void>(`/pages/${id}`, { method: "DELETE" });
}

export async function getRecentPages(): Promise<Page[]> {
  return apiFetch<Page[]>("/pages/recent");
}

export async function getWorkspaces(): Promise<string[]> {
  return apiFetch<string[]>("/pages/workspaces");
}

export async function searchPages(query: string): Promise<SearchResult[]> {
  return apiFetch<SearchResult[]>("/pages/search", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

export async function getWorkspaceMeta(): Promise<WorkspaceMeta[]> {
  return apiFetch<WorkspaceMeta[]>("/pages/workspaces/meta");
}

export async function createWorkspaceMeta(
  data: { name: string; icon?: string; color?: string; sort_order?: number },
): Promise<WorkspaceMeta> {
  return apiFetch<WorkspaceMeta>("/pages/workspaces/meta", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function reorderPages(
  pageIds: string[],
  workspace?: string,
): Promise<void> {
  await apiFetch<{ ok: boolean }>("/pages/reorder", {
    method: "POST",
    body: JSON.stringify({ page_ids: pageIds, workspace: workspace ?? null }),
  });
}

export function exportPageMd(page: Page): void {
  const blob = new Blob([`# ${page.title}\n\n${page.content}`], {
    type: "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${page.title.replace(/[^a-zA-Z0-9 _-]/g, "").trim().slice(0, 80) || "page"}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function exportPagePdf(pageId: string, title: string): Promise<void> {
  const res = await fetch(`/api/pages/${pageId}/export/pdf`);
  if (!res.ok) throw new Error("PDF export failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${title.replace(/[^a-zA-Z0-9 _-]/g, "").trim().slice(0, 80) || "page"}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}
