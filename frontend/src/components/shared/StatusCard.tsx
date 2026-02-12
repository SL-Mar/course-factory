import { cn } from "../../utils/cn";

interface StatusCardProps {
  ok: boolean;
  message: string;
  details?: Record<string, unknown>;
}

export function StatusCard({ ok, message, details }: StatusCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border p-3 text-sm",
        ok
          ? "border-green-500/20 bg-green-500/5 text-green-300"
          : "border-red-500/20 bg-red-500/5 text-red-300",
      )}
    >
      <p>{message}</p>
      {details && Object.keys(details).length > 0 && (
        <pre className="mt-2 overflow-x-auto text-xs text-gray-400 font-mono">
          {JSON.stringify(details, null, 2)}
        </pre>
      )}
    </div>
  );
}
