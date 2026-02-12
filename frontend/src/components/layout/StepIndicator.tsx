import { cn } from "../../utils/cn";
import { STEPS, STEP_LABELS, type Step } from "../../types/setup";

interface StepIndicatorProps {
  currentStep: Step;
  onStepClick?: (step: Step) => void;
}

export function StepIndicator({ currentStep, onStepClick }: StepIndicatorProps) {
  const currentIdx = STEPS.indexOf(currentStep);

  return (
    <div className="flex items-center justify-center gap-2">
      {STEPS.map((step, idx) => {
        const isActive = idx === currentIdx;
        const isComplete = idx < currentIdx;
        const isClickable = isComplete && onStepClick;

        return (
          <div key={step} className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => isClickable && onStepClick(step)}
              disabled={!isClickable}
              className={cn(
                "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-all duration-300",
                isActive && "bg-indigo-600/20 text-indigo-400 ring-1 ring-indigo-500/30",
                isComplete && "bg-green-500/10 text-green-400 cursor-pointer hover:bg-green-500/20",
                !isActive && !isComplete && "text-gray-600",
              )}
            >
              {isComplete ? (
                <svg className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              ) : (
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    isActive ? "bg-indigo-400" : "bg-gray-600",
                  )}
                />
              )}
              <span className="hidden sm:inline">{STEP_LABELS[step]}</span>
            </button>
            {idx < STEPS.length - 1 && (
              <div
                className={cn(
                  "h-px w-4",
                  idx < currentIdx ? "bg-green-500/30" : "bg-surface-border",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
