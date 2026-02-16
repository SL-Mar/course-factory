import { apiFetch } from "./client";
import type {
  Engine,
  EngineRunRequest,
  EngineRunResult,
  EngineStatus,
} from "../types";

export async function listEngines(): Promise<Engine[]> {
  return apiFetch<Engine[]>("/engines");
}

export async function runEngine(
  data: EngineRunRequest,
): Promise<EngineRunResult> {
  return apiFetch<EngineRunResult>("/engines", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getEngineStatus(name: string): Promise<EngineStatus> {
  return apiFetch<EngineStatus>(
    `/engines/status/${encodeURIComponent(name)}`,
  );
}
