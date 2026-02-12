export type Step =
  | "welcome"
  | "license"
  | "llm"
  | "services"
  | "notifications"
  | "review";

export const STEPS: Step[] = [
  "welcome",
  "license",
  "llm",
  "services",
  "notifications",
  "review",
];

export const STEP_LABELS: Record<Step, string> = {
  welcome: "Welcome",
  license: "License",
  llm: "LLM Config",
  services: "Services",
  notifications: "Notifications",
  review: "Review & Save",
};

export interface WizardState {
  currentStep: Step;
  license_key: string;
  licenseInfo: LicenseInfo | null;
  ollama_url: string;
  anthropic_api_key: string;
  openai_api_key: string;
  db_url: string;
  qdrant_url: string;
  redis_url: string;
  telegram_webhook: string;
}

export interface LicenseInfo {
  valid: boolean;
  email: string;
  product: string;
  tier: string;
  expiry: string;
  is_expired: boolean;
  error: string;
}

export interface ConnectionResult {
  ok: boolean;
  service: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface CurrentConfig {
  license_key: string;
  ollama_url: string;
  db_url: string;
  qdrant_url: string;
  redis_url: string;
  anthropic_api_key_set: boolean;
  openai_api_key_set: boolean;
  telegram_webhook: string;
}

export interface SaveResult {
  ok: boolean;
  path: string;
  error: string;
}

export type WizardAction =
  | { type: "SET_STEP"; step: Step }
  | { type: "SET_FIELD"; field: keyof WizardState; value: unknown }
  | { type: "SET_LICENSE_INFO"; info: LicenseInfo }
  | { type: "PREFILL"; config: CurrentConfig };
