import { apiFetch } from "./client";
import type {
  ChatRequest,
  ChatResponse,
  SlashCommand,
  CommandResponse,
} from "../types";

export async function sendChatMessage(
  data: ChatRequest,
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/ai/chat", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function runSlashCommand(
  data: SlashCommand,
): Promise<CommandResponse> {
  return apiFetch<CommandResponse>("/ai/command", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
