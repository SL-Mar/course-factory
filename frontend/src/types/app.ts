export type AppView = "dashboard" | "setup" | "workspace";

export type AppAction =
  | { type: "SET_VIEW"; view: AppView }
  | { type: "SET_ACTIVE_COURSE"; courseId: string };

export interface AppState {
  view: AppView;
  activeCourseId: string | null;
}
