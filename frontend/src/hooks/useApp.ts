import { useReducer, useCallback } from "react";
import type { AppState, AppAction, AppView } from "../types/app";

const initialState: AppState = {
  view: "dashboard",
  activeCourseId: null,
};

function reducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "SET_VIEW":
      return { ...state, view: action.view };
    case "SET_ACTIVE_COURSE":
      return { ...state, view: "workspace", activeCourseId: action.courseId };
    default:
      return state;
  }
}

export function useApp() {
  const [state, dispatch] = useReducer(reducer, initialState);

  const navigate = useCallback(
    (view: AppView) => dispatch({ type: "SET_VIEW", view }),
    [],
  );

  const openCourse = useCallback(
    (courseId: string) =>
      dispatch({ type: "SET_ACTIVE_COURSE", courseId }),
    [],
  );

  return { state, navigate, openCourse };
}
