import { useCallback } from "react";
import { InputField } from "../shared/InputField";
import { TestButton } from "../shared/TestButton";
import { ConnectionBadge } from "../shared/ConnectionBadge";
import { StatusCard } from "../shared/StatusCard";
import { StepNavigation } from "../shared/StepNavigation";
import { useConnectionTest } from "../../hooks/useConnectionTest";
import { testConnection } from "../../api/setup";
import type { WizardState } from "../../types/setup";

interface ServicesStepProps {
  state: WizardState;
  setField: (field: keyof WizardState, value: unknown) => void;
  onNext: () => void;
  onBack: () => void;
}

interface ServiceBlockProps {
  title: string;
  description: string;
  service: string;
  urlField: keyof WizardState;
  urlLabel: string;
  placeholder: string;
  state: WizardState;
  setField: (field: keyof WizardState, value: unknown) => void;
}

function ServiceBlock({
  title,
  description,
  service,
  urlField,
  urlLabel,
  placeholder,
  state,
  setField,
}: ServiceBlockProps) {
  const test = useConnectionTest(
    useCallback(
      () => testConnection(service, state[urlField] as string),
      [service, state[urlField]],
    ),
  );

  return (
    <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
          <p className="text-xs text-gray-500">{description}</p>
        </div>
        <ConnectionBadge status={test.status} />
      </div>
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <InputField
            label={urlLabel}
            value={state[urlField] as string}
            onChange={(v) => {
              setField(urlField, v);
              test.reset();
            }}
            placeholder={placeholder}
            mono
          />
        </div>
        <TestButton
          onClick={test.run}
          loading={test.status === "loading"}
        />
      </div>
      {test.result && (
        <StatusCard
          ok={test.result.ok}
          message={test.result.message}
          details={test.result.details ?? undefined}
        />
      )}
    </div>
  );
}

export function ServicesStep({
  state,
  setField,
  onNext,
  onBack,
}: ServicesStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">Services</h2>
        <p className="mt-1 text-sm text-gray-400">
          Configure and test connections to your infrastructure services.
        </p>
      </div>

      <ServiceBlock
        title="Database"
        description="PostgreSQL / TimescaleDB for course data"
        service="db"
        urlField="db_url"
        urlLabel="Connection String"
        placeholder="postgresql://cf:cf@localhost:5435/course_factory"
        state={state}
        setField={setField}
      />

      <ServiceBlock
        title="Qdrant"
        description="Vector store for knowledge embeddings"
        service="qdrant"
        urlField="qdrant_url"
        urlLabel="Qdrant URL"
        placeholder="http://localhost:6333"
        state={state}
        setField={setField}
      />

      <ServiceBlock
        title="Redis"
        description="Cache and message broker"
        service="redis"
        urlField="redis_url"
        urlLabel="Redis URL"
        placeholder="redis://localhost:6379/2"
        state={state}
        setField={setField}
      />

      <StepNavigation onBack={onBack} onNext={onNext} />
    </div>
  );
}
