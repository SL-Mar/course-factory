import { useCallback } from "react";
import { InputField } from "../shared/InputField";
import { SecretField } from "../shared/SecretField";
import { TestButton } from "../shared/TestButton";
import { ConnectionBadge } from "../shared/ConnectionBadge";
import { StatusCard } from "../shared/StatusCard";
import { StepNavigation } from "../shared/StepNavigation";
import { useConnectionTest } from "../../hooks/useConnectionTest";
import { testConnection } from "../../api/setup";
import type { WizardState } from "../../types/setup";

const CLOUD_MODEL_OPTIONS: Record<string, string[]> = {
  anthropic: ["claude-sonnet-4-5-20250929", "claude-haiku-3-5-20241022"],
  openai: ["gpt-4o", "gpt-4o-mini"],
};

interface LlmStepProps {
  state: WizardState;
  setField: (field: keyof WizardState, value: unknown) => void;
  onNext: () => void;
  onBack: () => void;
}

export function LlmStep({ state, setField, onNext, onBack }: LlmStepProps) {
  const ollamaTest = useConnectionTest(
    useCallback(
      () => testConnection("ollama", state.ollama_url),
      [state.ollama_url],
    ),
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">LLM Configuration</h2>
        <p className="mt-1 text-sm text-gray-400">
          Connect to your LLM providers. Ollama is required; cloud providers are
          optional.
        </p>
      </div>

      {/* Ollama */}
      <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-200">Ollama</h3>
            <p className="text-xs text-gray-500">Local LLM inference</p>
          </div>
          <ConnectionBadge status={ollamaTest.status} />
        </div>
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <InputField
              label="Ollama URL"
              value={state.ollama_url}
              onChange={(v) => {
                setField("ollama_url", v);
                ollamaTest.reset();
              }}
              placeholder="http://localhost:11434"
              mono
            />
          </div>
          <TestButton
            onClick={ollamaTest.run}
            loading={ollamaTest.status === "loading"}
          />
        </div>
        {ollamaTest.result && (
          <StatusCard
            ok={ollamaTest.result.ok}
            message={ollamaTest.result.message}
            details={ollamaTest.result.details ?? undefined}
          />
        )}
        <InputField
          label="Ollama Model"
          value={state.ollama_model}
          onChange={(v) => setField("ollama_model", v)}
          placeholder="qwen2.5:14b"
          mono
        />
      </div>

      {/* Cloud Providers */}
      <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-200">
            Cloud Providers
          </h3>
          <p className="text-xs text-gray-500">
            Optional. Leave blank to use Ollama only.
          </p>
        </div>
        <SecretField
          label="Anthropic API Key"
          value={state.anthropic_api_key}
          onChange={(v) => setField("anthropic_api_key", v)}
          placeholder="sk-ant-..."
          description="For Claude models via the Anthropic API"
        />
        <SecretField
          label="OpenAI API Key"
          value={state.openai_api_key}
          onChange={(v) => setField("openai_api_key", v)}
          placeholder="sk-..."
          description="For GPT models via the OpenAI API"
        />
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">
              Cloud Provider
            </label>
            <select
              value={state.cloud_provider}
              onChange={(e) => {
                setField("cloud_provider", e.target.value);
                setField(
                  "cloud_model",
                  e.target.value === "openai"
                    ? "gpt-4o"
                    : "claude-sonnet-4-5-20250929",
                );
              }}
              className="w-full rounded-lg border border-surface-border bg-surface px-3 py-2 text-sm text-gray-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="anthropic">Anthropic</option>
              <option value="openai">OpenAI</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">
              Cloud Model
            </label>
            <select
              value={
                CLOUD_MODEL_OPTIONS[state.cloud_provider]?.includes(
                  state.cloud_model,
                )
                  ? state.cloud_model
                  : "_custom"
              }
              onChange={(e) => {
                if (e.target.value !== "_custom") {
                  setField("cloud_model", e.target.value);
                }
              }}
              className="w-full rounded-lg border border-surface-border bg-surface px-3 py-2 text-sm text-gray-200 focus:border-indigo-500 focus:outline-none"
            >
              {(CLOUD_MODEL_OPTIONS[state.cloud_provider] ?? []).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
              {!CLOUD_MODEL_OPTIONS[state.cloud_provider]?.includes(
                state.cloud_model,
              ) && (
                <option value="_custom">{state.cloud_model} (custom)</option>
              )}
            </select>
          </div>
        </div>
      </div>

      <StepNavigation onBack={onBack} onNext={onNext} />
    </div>
  );
}
