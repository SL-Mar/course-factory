import { apiFetch } from "./client";
import type { GraphData, Backlink } from "../types";

export async function getFullGraph(): Promise<GraphData> {
  return apiFetch<GraphData>("/graph");
}

export async function getBacklinks(pageId: string): Promise<Backlink[]> {
  return apiFetch<Backlink[]>(`/graph/${pageId}/backlinks`);
}

export async function getNeighborhood(pageId: string): Promise<GraphData> {
  return apiFetch<GraphData>(`/graph/${pageId}/neighborhood`);
}
