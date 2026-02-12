import { cn } from "../../utils/cn";

interface InputFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  description?: string;
  placeholder?: string;
  mono?: boolean;
  disabled?: boolean;
}

export function InputField({
  label,
  value,
  onChange,
  description,
  placeholder,
  mono,
  disabled,
}: InputFieldProps) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-gray-300">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          "w-full rounded-lg border border-surface-border bg-surface px-3 py-2.5",
          "text-gray-100 placeholder-gray-600",
          "focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500",
          "transition-colors duration-200",
          "disabled:cursor-not-allowed disabled:opacity-50",
          mono && "font-mono text-sm",
        )}
      />
      {description && (
        <p className="text-xs text-gray-500">{description}</p>
      )}
    </div>
  );
}
