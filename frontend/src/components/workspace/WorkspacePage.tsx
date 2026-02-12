import { useWorkspace } from "../../hooks/useWorkspace";
import { FileTree } from "./FileTree";
import { ContentPanel } from "./ContentPanel";
import { CourseToolbar } from "./CourseToolbar";

interface WorkspacePageProps {
  courseId: string;
  onBack: () => void;
}

export function WorkspacePage({ courseId, onBack }: WorkspacePageProps) {
  const ws = useWorkspace(courseId);

  return (
    <div className="flex h-[calc(100vh-49px)] flex-col">
      <CourseToolbar
        title={ws.state.course?.title || ""}
        onBack={onBack}
        onRunStage={ws.runStage}
        stageStatus={ws.stageStatus}
        tokenData={ws.state.tokens}
      />
      <div className="flex flex-1 overflow-hidden">
        <div className="w-64 flex-shrink-0 overflow-y-auto border-r border-surface-border bg-surface p-2">
          <FileTree
            nodes={ws.state.tree}
            selectedPath={ws.state.selectedFile}
            onSelect={ws.selectFile}
          />
        </div>
        <div className="flex-1 overflow-y-auto">
          <ContentPanel
            selectedPath={ws.state.selectedFile}
            content={ws.state.fileContent}
            loading={ws.state.loading}
            editing={ws.state.editing}
            editContent={ws.state.editContent}
            onStartEdit={ws.startEdit}
            onCancelEdit={ws.cancelEdit}
            onEditChange={ws.setEditContent}
            onSave={ws.saveFile}
          />
        </div>
      </div>
    </div>
  );
}
