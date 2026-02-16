import { apiFetch } from "./client";
import type {
  TableDef,
  TableCreate,
  TableRow,
  TableQuery,
  TableQueryResult,
  TableTemplate,
} from "../types";

export async function listTables(): Promise<TableDef[]> {
  return apiFetch<TableDef[]>("/tables");
}

export async function createTable(data: TableCreate): Promise<TableDef> {
  return apiFetch<TableDef>("/tables", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getTable(name: string): Promise<TableDef> {
  return apiFetch<TableDef>(`/tables/${encodeURIComponent(name)}`);
}

export async function queryTable(
  name: string,
  query: TableQuery,
): Promise<TableQueryResult> {
  return apiFetch<TableQueryResult>(
    `/tables/${encodeURIComponent(name)}/query`,
    {
      method: "POST",
      body: JSON.stringify(query),
    },
  );
}

export async function insertRow(
  name: string,
  row: Record<string, unknown>,
): Promise<TableRow> {
  return apiFetch<TableRow>(
    `/tables/${encodeURIComponent(name)}/rows`,
    {
      method: "POST",
      body: JSON.stringify(row),
    },
  );
}

export async function getTableTemplates(): Promise<TableTemplate[]> {
  return apiFetch<TableTemplate[]>("/tables/templates");
}
