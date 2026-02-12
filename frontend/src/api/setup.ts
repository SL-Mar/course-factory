import { apiFetch } from "./client";
import type {
  ConnectionResult,
  CurrentConfig,
  LicenseInfo,
  SaveResult,
} from "../types/setup";

export function getCurrentConfig(): Promise<CurrentConfig> {
  return apiFetch<CurrentConfig>("/setup/current");
}

export function validateLicense(license_key: string): Promise<LicenseInfo> {
  return apiFetch<LicenseInfo>("/setup/validate-license", {
    method: "POST",
    body: JSON.stringify({ license_key }),
  });
}

export function testConnection(
  service: string,
  url: string,
): Promise<ConnectionResult> {
  return apiFetch<ConnectionResult>("/setup/test-connection", {
    method: "POST",
    body: JSON.stringify({ service, url }),
  });
}

export function testTelegram(webhook_url: string): Promise<ConnectionResult> {
  return apiFetch<ConnectionResult>("/setup/test-telegram", {
    method: "POST",
    body: JSON.stringify({ webhook_url }),
  });
}

export function saveConfig(config: {
  license_key: string;
  ollama_url: string;
  anthropic_api_key: string;
  openai_api_key: string;
  db_url: string;
  qdrant_url: string;
  redis_url: string;
  telegram_webhook: string;
  ollama_model: string;
  cloud_provider: string;
  cloud_model: string;
}): Promise<SaveResult> {
  return apiFetch<SaveResult>("/setup/save", {
    method: "POST",
    body: JSON.stringify(config),
  });
}
