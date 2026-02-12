import { useState } from "react";
import { StepNavigation } from "../shared/StepNavigation";
import { StatusCard } from "../shared/StatusCard";
import { saveConfig } from "../../api/setup";
import type { WizardState } from "../../types/setup";

interface ReviewStepProps {
  state: WizardState;
  onBack: () => void;
}

function ReviewRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <span className="text-sm text-gray-400 shrink-0">{label}</span>
      <span
        className={`text-sm text-gray-200 text-right break-all ${mono ? "font-mono" : ""}`}
      >
        {value || <span className="text-gray-600">Not set</span>}
      </span>
    </div>
  );
}

export function ReviewStep({ state, onBack }: ReviewStepProps) {
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<{
    ok: boolean;
    message: string;
  } | null>(null);

  const handleSave = async () => {
    setSaving(true);
    setSaveResult(null);
    try {
      const result = await saveConfig({
        license_key: state.license_key,
        ollama_url: state.ollama_url,
        anthropic_api_key: state.anthropic_api_key,
        openai_api_key: state.openai_api_key,
        db_url: state.db_url,
        qdrant_url: state.qdrant_url,
        redis_url: state.redis_url,
        telegram_webhook: state.telegram_webhook,
        ollama_model: state.ollama_model,
        cloud_provider: state.cloud_provider,
        cloud_model: state.cloud_model,
      });
      if (result.ok) {
        setSaveResult({
          ok: true,
          message: `Configuration saved to ${result.path}`,
        });
      } else {
        setSaveResult({
          ok: false,
          message: result.error || "Failed to save configuration.",
        });
      }
    } catch (err) {
      setSaveResult({
        ok: false,
        message: err instanceof Error ? err.message : "Save failed.",
      });
    } finally {
      setSaving(false);
    }
  };

  const licenseStatus = state.licenseInfo?.valid
    ? state.licenseInfo.is_expired
      ? "Valid (expired)"
      : `Valid - ${state.licenseInfo.email}`
    : state.license_key
      ? "Not validated"
      : "Not set";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">Review & Save</h2>
        <p className="mt-1 text-sm text-gray-400">
          Review your configuration and save to disk.
        </p>
      </div>

      {/* License */}
      <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-1">
        <h3 className="text-sm font-semibold text-gray-300 mb-2">License</h3>
        <ReviewRow label="Status" value={licenseStatus} />
        {state.licenseInfo?.valid && (
          <>
            <ReviewRow label="Product" value={state.licenseInfo.product} />
            <ReviewRow label="Tier" value={state.licenseInfo.tier} />
            <ReviewRow
              label="Expires"
              value={state.licenseInfo.expiry.split("T")[0]}
            />
          </>
        )}
      </div>

      {/* LLM */}
      <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-1">
        <h3 className="text-sm font-semibold text-gray-300 mb-2">
          LLM Providers
        </h3>
        <ReviewRow label="Ollama" value={state.ollama_url} mono />
        <ReviewRow label="Ollama Model" value={state.ollama_model} mono />
        <ReviewRow
          label="Anthropic"
          value={state.anthropic_api_key ? "Configured" : "Not set"}
        />
        <ReviewRow
          label="OpenAI"
          value={state.openai_api_key ? "Configured" : "Not set"}
        />
        <ReviewRow label="Cloud Provider" value={state.cloud_provider} />
        <ReviewRow label="Cloud Model" value={state.cloud_model} mono />
      </div>

      {/* Services */}
      <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-1">
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Services</h3>
        <ReviewRow label="Database" value={state.db_url} mono />
        <ReviewRow label="Qdrant" value={state.qdrant_url} mono />
        <ReviewRow label="Redis" value={state.redis_url} mono />
      </div>

      {/* Notifications */}
      <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-1">
        <h3 className="text-sm font-semibold text-gray-300 mb-2">
          Notifications
        </h3>
        <ReviewRow label="Telegram" value={state.telegram_webhook} mono />
      </div>

      {saveResult && (
        <StatusCard ok={saveResult.ok} message={saveResult.message} />
      )}

      <StepNavigation
        onBack={onBack}
        onNext={handleSave}
        nextLabel="Save Configuration"
        saving={saving}
        nextDisabled={saving}
      />
    </div>
  );
}
