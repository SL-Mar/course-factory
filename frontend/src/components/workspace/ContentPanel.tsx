import { cn } from "../../utils/cn";
import { isMarkdownFile } from "../../utils/fileType";
import { MarkdownViewer } from "./MarkdownViewer";

interface ContentPanelProps {
  selectedPath: string | null;
  content: string;
  loading: boolean;
  editing: boolean;
  editContent: string;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onEditChange: (content: string) => void;
  onSave: () => void;
}

export function ContentPanel({
  selectedPath,
  content,
  loading,
  editing,
  editContent,
  onStartEdit,
  onCancelEdit,
  onEditChange,
  onSave,
}: ContentPanelProps) {
  if (!selectedPath) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-gray-600">
          Select a file to view its content
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-surface-border px-4 py-2">
        <span className="text-xs font-mono text-gray-400">{selectedPath}</span>
        <div className="flex items-center gap-2">
          {editing ? (
            <>
              <button
                onClick={onCancelEdit}
                className="rounded-md border border-surface-border px-2.5 py-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={onSave}
                className="rounded-md bg-indigo-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-indigo-500 transition-colors"
              >
                Save
              </button>
            </>
          ) : (
            <button
              onClick={onStartEdit}
              className="rounded-md border border-surface-border px-2.5 py-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
            >
              Edit
            </button>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {editing ? (
          <textarea
            value={editContent}
            onChange={(e) => onEditChange(e.target.value)}
            className={cn(
              "h-full w-full resize-none rounded-lg border border-surface-border bg-surface p-3",
              "font-mono text-sm text-gray-200 leading-relaxed",
              "focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500",
            )}
            spellCheck={false}
          />
        ) : selectedPath && isMarkdownFile(selectedPath) ? (
          <MarkdownViewer content={content} />
        ) : (
          <pre className="whitespace-pre-wrap font-mono text-sm text-gray-300 leading-relaxed">
            {content}
          </pre>
        )}
      </div>
    </div>
  );
}
