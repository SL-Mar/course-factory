import { Fragment } from "react";
import type { CourseTokens, StageStatus } from "../../types/workspace";
import { cn } from "../../utils/cn";

function formatTokenCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

interface CourseToolbarProps {
  title: string;
  onBack: () => void;
  onRunStage: (stage: string) => void;
  stageStatus: (stage: string) => StageStatus;
  tokenData: CourseTokens | null;
}

const STAGES = [
  { key: "knowledge", label: "Ingest Sources" },
  { key: "discovery", label: "Generate Proposal" },
  { key: "research", label: "Approve & Research" },
  { key: "synthesis", label: "Write Scripts" },
  { key: "production", label: "Generate Slides" },
];

export function CourseToolbar({
  title,
  onBack,
  onRunStage,
  stageStatus,
  tokenData,
}: CourseToolbarProps) {
  const totalTokens = tokenData?.total?.total_tokens ?? 0;
  const totalCost = tokenData?.total?.estimated_cost_usd ?? 0;
  return (
    <div className="flex items-center gap-3 border-b border-surface-border px-4 py-2">
      <button
        onClick={onBack}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
      >
        <svg
          className="h-3.5 w-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Dashboard
      </button>
      <span className="text-xs text-gray-600">|</span>
      <h2 className="text-sm font-medium text-gray-200 truncate flex-1">
        {title}
      </h2>
      <div className="flex items-center gap-2">
        {STAGES.map((s, i) => {
          const st = stageStatus(s.key);
          return (
            <Fragment key={s.key}>
              {i === 2 && (
                <span className="mx-1 h-4 w-px bg-surface-border" />
              )}
              <StageButton
                label={s.label}
                status={st}
                onClick={() => onRunStage(s.key)}
              />
            </Fragment>
          );
        })}
      </div>
      {totalTokens > 0 && (
        <div className="flex items-center gap-2 text-xs text-gray-400 shrink-0 ml-2">
          <span>{formatTokenCount(totalTokens)} tokens</span>
          {totalCost > 0 && (
            <span className="text-amber-400">
              ${totalCost.toFixed(4)}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

function StageButton({
  label,
  status,
  onClick,
}: {
  label: string;
  status: StageStatus;
  onClick: () => void;
}) {
  const isRunning = status.status === "running";
  const isDone = status.status === "done";
  const isError = status.status === "error";

  return (
    <button
      onClick={onClick}
      disabled={isRunning}
      title={status.message || label}
      className={cn(
        "rounded-lg border px-3 py-1.5 text-xs font-medium transition-all",
        isRunning &&
          "border-indigo-500/50 text-indigo-300 animate-pulse cursor-wait",
        isDone && "border-green-500/50 text-green-300",
        isError && "border-red-500/50 text-red-300",
        !isRunning &&
          !isDone &&
          !isError &&
          "border-surface-border text-gray-400 hover:text-gray-200 hover:border-gray-600",
        isRunning && "cursor-not-allowed",
      )}
    >
      {isRunning ? (
        <span className="flex items-center gap-1.5">
          <svg
            className="h-3 w-3 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          Running...
        </span>
      ) : isDone ? (
        <span className="flex items-center gap-1.5">
          <svg
            className="h-3 w-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 13l4 4L19 7"
            />
          </svg>
          {label}
        </span>
      ) : (
        label
      )}
    </button>
  );
}
