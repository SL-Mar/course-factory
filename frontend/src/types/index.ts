/* ── Page ── */

export interface Page {
  id: string;
  title: string;
  content: string;
  workspace: string;
  tags: string[];
  parent_id: string | null;
  is_favorite: boolean;
  is_trashed: boolean;
  icon: string | null;
  cover: string | null;
  word_count?: number;
  created_at: string;
  updated_at: string;
  children?: Page[];
}

export interface PageCreate {
  title: string;
  content?: string;
  workspace?: string;
  tags?: string[];
  parent_id?: string | null;
  icon?: string | null;
  cover?: string | null;
}

export interface PageUpdate {
  title?: string;
  content?: string;
  workspace?: string;
  tags?: string[];
  parent_id?: string | null;
  is_favorite?: boolean;
  is_trashed?: boolean;
  icon?: string | null;
  cover?: string | null;
}

export interface PageListResponse {
  pages: Page[];
  total: number;
}

export interface SearchResult {
  page: Page;
  score: number;
  snippet: string;
}

/* ── Table ── */

export interface TableColumn {
  name: string;
  type: string;
  options?: string[];
}

export interface TableDef {
  name: string;
  columns: TableColumn[];
  row_count: number;
  created_at: string;
}

export interface TableCreate {
  name: string;
  columns: TableColumn[];
}

export interface TableRow {
  id: string;
  [key: string]: unknown;
}

export interface TableQuery {
  filters?: Record<string, unknown>;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface TableQueryResult {
  rows: TableRow[];
  total: number;
}

export interface TableTemplate {
  name: string;
  description: string;
  columns: TableColumn[];
}

/* ── Graph ── */

export interface GraphNode {
  id: string;
  title: string;
  workspace: string;
  tags: string[];
  link_count: number;
}

export interface GraphLink {
  source: string;
  target: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface Backlink {
  page_id: string;
  page_title: string;
  context: string;
}

/* ── AI ── */

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  include_context?: boolean;
}

export interface ChatResponse {
  response: string;
  context_pages?: string[];
}

export interface SlashCommand {
  command: string;
  args?: string;
  page_id?: string;
}

export interface CommandResponse {
  result: string;
  modified_content?: string;
}

/* ── Engines ── */

export interface Engine {
  name: string;
  description: string;
  status: "idle" | "running" | "error";
  last_run?: string;
}

export interface EngineRunRequest {
  name: string;
  params?: Record<string, unknown>;
}

export interface EngineRunResult {
  name: string;
  status: "success" | "error";
  message: string;
  duration_ms: number;
}

export interface EngineStatus {
  name: string;
  status: "idle" | "running" | "error";
  progress?: number;
  message?: string;
}

/* ── Import ── */

export interface ImportResult {
  imported: number;
  errors: string[];
}

/* ── App State ── */

export type View =
  | "pages"
  | "page-editor"
  | "tables"
  | "table-view"
  | "graph"
  | "ai-chat"
  | "engines"
  | "trash";

export interface AppState {
  view: View;
  activePage: Page | null;
  activeTable: string | null;
  activeWorkspace: string;
  sidebarCollapsed: boolean;
  searchOpen: boolean;
}
