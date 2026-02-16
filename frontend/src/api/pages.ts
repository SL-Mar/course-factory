import { apiFetch } from "./client";
import type {
  Page,
  PageCreate,
  PageUpdate,
  PageListResponse,
  SearchResult,
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
