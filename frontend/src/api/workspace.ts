import { apiFetch } from "./client";
import type { FileNode, StageStatus } from "../types/workspace";

interface FileTreeResponse {
  tree: FileNode[];
}

interface FileContentResponse {
  path: string;
  content: string;
}

export function getFileTree(courseId: string): Promise<FileNode[]> {
  return apiFetch<FileTreeResponse>(
    `/courses/${courseId}/workspace/tree`,
  ).then((r) => r.tree);
}

export function getFileContent(
  courseId: string,
  path: string,
): Promise<string> {
  return apiFetch<FileContentResponse>(
    `/courses/${courseId}/workspace/file?path=${encodeURIComponent(path)}`,
  ).then((r) => r.content);
}

export function saveFileContent(
  courseId: string,
  path: string,
  content: string,
): Promise<void> {
  return apiFetch(`/courses/${courseId}/workspace/file`, {
    method: "PUT",
    body: JSON.stringify({ path, content }),
  });
}

export function triggerStage(
  courseId: string,
  stageName: string,
): Promise<void> {
  return apiFetch(`/courses/${courseId}/workspace/stage/${stageName}`, {
    method: "POST",
  });
}

export function getStageStatus(
  courseId: string,
  stageName: string,
): Promise<StageStatus> {
  return apiFetch<StageStatus>(
    `/courses/${courseId}/workspace/stage/${stageName}/status`,
  );
}
