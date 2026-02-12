import { cn } from "../../utils/cn";

type Status = "idle" | "loading" | "success" | "error";

interface ConnectionBadgeProps {
  status: Status;
  label?: string;
}

export function ConnectionBadge({ status, label }: ConnectionBadgeProps) {
  if (status === "idle") return null;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        status === "loading" && "bg-yellow-500/10 text-yellow-400",
        status === "success" && "bg-green-500/10 text-green-400",
        status === "error" && "bg-red-500/10 text-red-400",
      )}
    >
      {status === "loading" && (
        <svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {status === "success" && (
        <span className="h-1.5 w-1.5 rounded-full bg-green-400" />
      )}
      {status === "error" && (
        <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
      )}
      {label ?? (status === "loading" ? "Testing..." : status === "success" ? "Connected" : "Failed")}
    </span>
  );
}
