import { WizardLayout } from "./components/layout/WizardLayout";
import { WelcomeStep } from "./components/steps/WelcomeStep";
import { LicenseStep } from "./components/steps/LicenseStep";
import { LlmStep } from "./components/steps/LlmStep";
import { ServicesStep } from "./components/steps/ServicesStep";
import { NotificationsStep } from "./components/steps/NotificationsStep";
import { ReviewStep } from "./components/steps/ReviewStep";
import { useSetupWizard } from "./hooks/useSetupWizard";

export default function App() {
  const { state, dispatch, setField, goNext, goBack, goTo } =
    useSetupWizard();

  const stepContent = () => {
    switch (state.currentStep) {
      case "welcome":
        return <WelcomeStep onNext={goNext} />;
      case "license":
        return (
          <LicenseStep
            state={state}
            setField={setField}
            dispatch={dispatch}
            onNext={goNext}
            onBack={goBack}
          />
        );
      case "llm":
        return (
          <LlmStep
            state={state}
            setField={setField}
            onNext={goNext}
            onBack={goBack}
          />
        );
      case "services":
        return (
          <ServicesStep
            state={state}
            setField={setField}
            onNext={goNext}
            onBack={goBack}
          />
        );
      case "notifications":
        return (
          <NotificationsStep
            state={state}
            setField={setField}
            onNext={goNext}
            onBack={goBack}
          />
        );
      case "review":
        return <ReviewStep state={state} onBack={goBack} />;
    }
  };

  return (
    <WizardLayout currentStep={state.currentStep} onStepClick={goTo}>
      {stepContent()}
    </WizardLayout>
  );
}
