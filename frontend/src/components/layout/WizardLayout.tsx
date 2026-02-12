import type { ReactNode } from "react";
import { StepIndicator } from "./StepIndicator";
import type { Step } from "../../types/setup";

interface WizardLayoutProps {
  currentStep: Step;
  onStepClick?: (step: Step) => void;
  children: ReactNode;
}

export function WizardLayout({
  currentStep,
  onStepClick,
  children,
}: WizardLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b border-surface-border px-6 py-4">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
              CF
            </div>
            <span className="text-sm font-semibold text-gray-300">
              Course Factory
            </span>
          </div>
          <StepIndicator
            currentStep={currentStep}
            onStepClick={onStepClick}
          />
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 px-6 py-10">
        <div className="mx-auto max-w-2xl">{children}</div>
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-border px-6 py-3">
        <p className="text-center text-xs text-gray-600">
          Course Factory v0.1.0
        </p>
      </footer>
    </div>
  );
}
