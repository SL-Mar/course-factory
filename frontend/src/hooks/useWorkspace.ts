import { useReducer, useEffect, useCallback, useRef } from "react";
import type {
  WorkspaceState,
  WorkspaceAction,
  StageStatus,
} from "../types/workspace";
import {
  getFileTree,
  getFileContent,
  saveFileContent,
  triggerStage,
  getStageStatus,
} from "../api/workspace";
import { getCourse } from "../api/courses";

const initialState: WorkspaceState = {
  course: null,
  tree: [],
  selectedFile: null,
  fileContent: "",
  editing: false,
  editContent: "",
  loading: false,
  stages: {},
};

function reducer(
  state: WorkspaceState,
  action: WorkspaceAction,
): WorkspaceState {
  switch (action.type) {
    case "SET_COURSE":
      return { ...state, course: action.course };
    case "SET_TREE":
      return { ...state, tree: action.tree };
    case "SELECT_FILE":
      return {
        ...state,
        selectedFile: action.path,
        editing: false,
        editContent: "",
      };
    case "SET_FILE_CONTENT":
      return { ...state, fileContent: action.content, loading: false };
    case "SET_EDITING":
      return {
        ...state,
        editing: action.editing,
        editContent: action.editing ? state.fileContent : "",
      };
    case "SET_EDIT_CONTENT":
      return { ...state, editContent: action.content };
    case "SET_LOADING":
      return { ...state, loading: action.loading };
    case "SET_STAGE_STATUS":
      return {
        ...state,
        stages: { ...state.stages, [action.stage]: action.status },
      };
    default:
      return state;
  }
}

export function useWorkspace(courseId: string) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const pollRef = useRef<Record<string, number>>({});

  // Load course and tree on mount
  useEffect(() => {
    getCourse(courseId)
      .then((course) => dispatch({ type: "SET_COURSE", course }))
      .catch(() => {});
    refreshTree();
    return () => {
      // cleanup poll intervals
      Object.values(pollRef.current).forEach(clearInterval);
    };
  }, [courseId]);

  const refreshTree = useCallback(() => {
    getFileTree(courseId)
      .then((tree) => dispatch({ type: "SET_TREE", tree }))
      .catch(() => {});
  }, [courseId]);

  // Load file content when selected
  useEffect(() => {
    if (!state.selectedFile) return;
    dispatch({ type: "SET_LOADING", loading: true });
    getFileContent(courseId, state.selectedFile)
      .then((content) => dispatch({ type: "SET_FILE_CONTENT", content }))
      .catch(() => dispatch({ type: "SET_LOADING", loading: false }));
  }, [courseId, state.selectedFile]);

  const selectFile = useCallback(
    (path: string) => dispatch({ type: "SELECT_FILE", path }),
    [],
  );

  const startEdit = useCallback(
    () => dispatch({ type: "SET_EDITING", editing: true }),
    [],
  );

  const cancelEdit = useCallback(
    () => dispatch({ type: "SET_EDITING", editing: false }),
    [],
  );

  const setEditContent = useCallback(
    (content: string) => dispatch({ type: "SET_EDIT_CONTENT", content }),
    [],
  );

  const saveFile = useCallback(async () => {
    if (!state.selectedFile) return;
    await saveFileContent(courseId, state.selectedFile, state.editContent);
    dispatch({ type: "SET_FILE_CONTENT", content: state.editContent });
    dispatch({ type: "SET_EDITING", editing: false });
  }, [courseId, state.selectedFile, state.editContent]);

  const runStage = useCallback(
    async (stageName: string) => {
      dispatch({
        type: "SET_STAGE_STATUS",
        stage: stageName,
        status: { status: "running", message: `Starting ${stageName}...` },
      });
      try {
        await triggerStage(courseId, stageName);
      } catch {
        dispatch({
          type: "SET_STAGE_STATUS",
          stage: stageName,
          status: { status: "error", message: "Failed to start stage" },
        });
        return;
      }

      // Poll for status
      const id = window.setInterval(async () => {
        try {
          const s = await getStageStatus(courseId, stageName);
          dispatch({
            type: "SET_STAGE_STATUS",
            stage: stageName,
            status: s,
          });
          if (s.status === "done" || s.status === "error") {
            clearInterval(id);
            delete pollRef.current[stageName];
            refreshTree();
          }
        } catch {
          clearInterval(id);
          delete pollRef.current[stageName];
        }
      }, 3000);
      pollRef.current[stageName] = id;
    },
    [courseId, refreshTree],
  );

  const stageStatus = useCallback(
    (stageName: string): StageStatus =>
      state.stages[stageName] || { status: "idle", message: "" },
    [state.stages],
  );

  return {
    state,
    selectFile,
    startEdit,
    cancelEdit,
    setEditContent,
    saveFile,
    runStage,
    stageStatus,
    refreshTree,
  };
}
