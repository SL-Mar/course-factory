import { apiFetch } from "./client";
import type { GraphData, Backlink } from "../types";

export async function getFullGraph(workspace?: string): Promise<GraphData> {
  const qs = workspace ? `?workspace=${encodeURIComponent(workspace)}` : "";
  return apiFetch<GraphData>(`/graph${qs}`);
}

export async function getBacklinks(pageId: string): Promise<Backlink[]> {
  return apiFetch<Backlink[]>(`/graph/${pageId}/backlinks`);
}

export async function getNeighborhood(pageId: string): Promise<GraphData> {
  return apiFetch<GraphData>(`/graph/${pageId}/neighborhood`);
}
