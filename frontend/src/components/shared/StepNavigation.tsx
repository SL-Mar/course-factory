import { cn } from "../../utils/cn";

interface StepNavigationProps {
  onBack?: () => void;
  onNext?: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  showBack?: boolean;
  saving?: boolean;
}

export function StepNavigation({
  onBack,
  onNext,
  nextLabel = "Next",
  nextDisabled,
  showBack = true,
  saving,
}: StepNavigationProps) {
  return (
    <div className="flex items-center justify-between pt-6">
      {showBack && onBack ? (
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg px-4 py-2.5 text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors"
        >
          Back
        </button>
      ) : (
        <div />
      )}
      {onNext && (
        <button
          type="button"
          onClick={onNext}
          disabled={nextDisabled || saving}
          className={cn(
            "rounded-lg px-6 py-2.5 text-sm font-medium transition-all duration-200",
            "bg-indigo-600 text-white hover:bg-indigo-500",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          {saving ? (
            <span className="flex items-center gap-2">
              <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Saving...
            </span>
          ) : (
            nextLabel
          )}
        </button>
      )}
    </div>
  );
}
