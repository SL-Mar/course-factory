import { cn } from "../../utils/cn";

interface TestButtonProps {
  onClick: () => void;
  loading?: boolean;
  disabled?: boolean;
  label?: string;
}

export function TestButton({
  onClick,
  loading,
  disabled,
  label = "Test Connection",
}: TestButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className={cn(
        "rounded-lg border border-surface-border px-3 py-2 text-sm font-medium",
        "text-gray-300 hover:bg-surface-hover hover:text-gray-100",
        "transition-all duration-200",
        "disabled:cursor-not-allowed disabled:opacity-50",
      )}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Testing...
        </span>
      ) : (
        label
      )}
    </button>
  );
}
