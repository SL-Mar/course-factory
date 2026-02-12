export interface CourseSource {
  type: "notion" | "github" | "url";
  id?: string;
  owner?: string;
  repo?: string;
  url?: string;
}

export interface Course {
  id: string;
  title: string;
  description: string;
  sources: CourseSource[];
}

export interface FileNode {
  name: string;
  path: string;
  type: "file" | "directory";
  children?: FileNode[];
}

export interface StageStatus {
  status: "idle" | "running" | "done" | "error";
  message: string;
}

export interface TokenUsage {
  stage: string;
  calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface CourseTokens {
  stages: Record<string, TokenUsage>;
  total: TokenUsage | null;
}

export interface WorkspaceState {
  course: Course | null;
  tree: FileNode[];
  selectedFile: string | null;
  fileContent: string;
  editing: boolean;
  editContent: string;
  loading: boolean;
  stages: Record<string, StageStatus>;
  tokens: CourseTokens | null;
}

export type WorkspaceAction =
  | { type: "SET_COURSE"; course: Course }
  | { type: "SET_TREE"; tree: FileNode[] }
  | { type: "SELECT_FILE"; path: string }
  | { type: "SET_FILE_CONTENT"; content: string }
  | { type: "SET_EDITING"; editing: boolean }
  | { type: "SET_EDIT_CONTENT"; content: string }
  | { type: "SET_LOADING"; loading: boolean }
  | { type: "SET_STAGE_STATUS"; stage: string; status: StageStatus }
  | { type: "SET_TOKENS"; tokens: CourseTokens };
