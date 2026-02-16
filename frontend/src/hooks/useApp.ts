import { useCallback, useReducer } from "react";
import type { AppState, View, Page } from "../types";

type Action =
  | { type: "SET_VIEW"; view: View }
  | { type: "SET_ACTIVE_PAGE"; page: Page | null }
  | { type: "SET_ACTIVE_TABLE"; table: string | null }
  | { type: "SET_WORKSPACE"; workspace: string }
  | { type: "TOGGLE_SIDEBAR" }
  | { type: "OPEN_SEARCH" }
  | { type: "CLOSE_SEARCH" };

const initialState: AppState = {
  view: "pages",
  activePage: null,
  activeTable: null,
  activeWorkspace: "default",
  sidebarCollapsed: false,
  searchOpen: false,
};

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "SET_VIEW":
      return { ...state, view: action.view };
    case "SET_ACTIVE_PAGE":
      return { ...state, activePage: action.page };
    case "SET_ACTIVE_TABLE":
      return { ...state, activeTable: action.table };
    case "SET_WORKSPACE":
      return { ...state, activeWorkspace: action.workspace };
    case "TOGGLE_SIDEBAR":
      return { ...state, sidebarCollapsed: !state.sidebarCollapsed };
    case "OPEN_SEARCH":
      return { ...state, searchOpen: true };
    case "CLOSE_SEARCH":
      return { ...state, searchOpen: false };
    default:
      return state;
  }
}

export function useApp() {
  const [state, dispatch] = useReducer(reducer, initialState);

  const navigate = useCallback((view: View) => {
    dispatch({ type: "SET_VIEW", view });
  }, []);

  const openPage = useCallback((page: Page) => {
    dispatch({ type: "SET_ACTIVE_PAGE", page });
    dispatch({ type: "SET_VIEW", view: "page-editor" });
  }, []);

  const closePage = useCallback(() => {
    dispatch({ type: "SET_ACTIVE_PAGE", page: null });
    dispatch({ type: "SET_VIEW", view: "pages" });
  }, []);

  const openTable = useCallback((name: string) => {
    dispatch({ type: "SET_ACTIVE_TABLE", table: name });
    dispatch({ type: "SET_VIEW", view: "table-view" });
  }, []);

  const setWorkspace = useCallback((workspace: string) => {
    dispatch({ type: "SET_WORKSPACE", workspace });
  }, []);

  const toggleSidebar = useCallback(() => {
    dispatch({ type: "TOGGLE_SIDEBAR" });
  }, []);

  const openSearch = useCallback(() => {
    dispatch({ type: "OPEN_SEARCH" });
  }, []);

  const closeSearch = useCallback(() => {
    dispatch({ type: "CLOSE_SEARCH" });
  }, []);

  return {
    state,
    navigate,
    openPage,
    closePage,
    openTable,
    setWorkspace,
    toggleSidebar,
    openSearch,
    closeSearch,
  };
}
