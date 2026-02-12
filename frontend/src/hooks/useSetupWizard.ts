import { useReducer, useEffect, useCallback } from "react";
import type { WizardState, WizardAction, Step, CurrentConfig } from "../types/setup";
import { STEPS } from "../types/setup";
import { getCurrentConfig } from "../api/setup";

const initialState: WizardState = {
  currentStep: "welcome",
  license_key: "",
  licenseInfo: null,
  ollama_url: "http://localhost:11434",
  anthropic_api_key: "",
  openai_api_key: "",
  db_url: "postgresql://cf:cf@localhost:5435/course_factory",
  qdrant_url: "http://localhost:6333",
  redis_url: "redis://localhost:6379/2",
  telegram_webhook: "http://localhost:5678/webhook/send-telegram",
};

function reducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "SET_STEP":
      return { ...state, currentStep: action.step };
    case "SET_FIELD":
      return { ...state, [action.field]: action.value };
    case "SET_LICENSE_INFO":
      return { ...state, licenseInfo: action.info };
    case "PREFILL": {
      const c = action.config;
      return {
        ...state,
        license_key: c.license_key || state.license_key,
        ollama_url: c.ollama_url || state.ollama_url,
        db_url: c.db_url || state.db_url,
        qdrant_url: c.qdrant_url || state.qdrant_url,
        redis_url: c.redis_url || state.redis_url,
        telegram_webhook: c.telegram_webhook || state.telegram_webhook,
      };
    }
    default:
      return state;
  }
}

export function useSetupWizard() {
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    getCurrentConfig()
      .then((config: CurrentConfig) => dispatch({ type: "PREFILL", config }))
      .catch(() => {});
  }, []);

  const setField = useCallback(
    (field: keyof WizardState, value: unknown) =>
      dispatch({ type: "SET_FIELD", field, value }),
    [],
  );

  const goNext = useCallback(() => {
    const idx = STEPS.indexOf(state.currentStep);
    if (idx < STEPS.length - 1) {
      dispatch({ type: "SET_STEP", step: STEPS[idx + 1] });
    }
  }, [state.currentStep]);

  const goBack = useCallback(() => {
    const idx = STEPS.indexOf(state.currentStep);
    if (idx > 0) {
      dispatch({ type: "SET_STEP", step: STEPS[idx - 1] });
    }
  }, [state.currentStep]);

  const goTo = useCallback(
    (step: Step) => dispatch({ type: "SET_STEP", step }),
    [],
  );

  return { state, dispatch, setField, goNext, goBack, goTo };
}
