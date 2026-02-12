import { useCallback } from "react";
import { InputField } from "../shared/InputField";
import { TestButton } from "../shared/TestButton";
import { ConnectionBadge } from "../shared/ConnectionBadge";
import { StatusCard } from "../shared/StatusCard";
import { StepNavigation } from "../shared/StepNavigation";
import { useConnectionTest } from "../../hooks/useConnectionTest";
import { testTelegram } from "../../api/setup";
import type { WizardState } from "../../types/setup";

interface NotificationsStepProps {
  state: WizardState;
  setField: (field: keyof WizardState, value: unknown) => void;
  onNext: () => void;
  onBack: () => void;
}

export function NotificationsStep({
  state,
  setField,
  onNext,
  onBack,
}: NotificationsStepProps) {
  const telegramTest = useConnectionTest(
    useCallback(
      () => testTelegram(state.telegram_webhook),
      [state.telegram_webhook],
    ),
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">Notifications</h2>
        <p className="mt-1 text-sm text-gray-400">
          Configure Telegram notifications for pipeline events and alerts.
        </p>
      </div>

      <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-200">Telegram</h3>
            <p className="text-xs text-gray-500">
              Via n8n webhook
            </p>
          </div>
          <ConnectionBadge status={telegramTest.status} />
        </div>
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <InputField
              label="Webhook URL"
              value={state.telegram_webhook}
              onChange={(v) => {
                setField("telegram_webhook", v);
                telegramTest.reset();
              }}
              placeholder="http://localhost:5678/webhook/send-telegram"
              mono
            />
          </div>
          <TestButton
            onClick={telegramTest.run}
            loading={telegramTest.status === "loading"}
            label="Send Test"
          />
        </div>
        {telegramTest.result && (
          <StatusCard
            ok={telegramTest.result.ok}
            message={telegramTest.result.message}
          />
        )}
      </div>

      <StepNavigation onBack={onBack} onNext={onNext} />
    </div>
  );
}
