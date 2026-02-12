import { AppShell } from "./components/layout/AppShell";
import { WizardLayout } from "./components/layout/WizardLayout";
import { WelcomeStep } from "./components/steps/WelcomeStep";
import { LicenseStep } from "./components/steps/LicenseStep";
import { LlmStep } from "./components/steps/LlmStep";
import { ServicesStep } from "./components/steps/ServicesStep";
import { NotificationsStep } from "./components/steps/NotificationsStep";
import { ReviewStep } from "./components/steps/ReviewStep";
import { Dashboard } from "./components/dashboard/Dashboard";
import { WorkspacePage } from "./components/workspace/WorkspacePage";
import { useApp } from "./hooks/useApp";
import { useSetupWizard } from "./hooks/useSetupWizard";

export default function App() {
  const { state: appState, navigate, openCourse } = useApp();
  const wizard = useSetupWizard();

  const renderSetup = () => {
    const { state, dispatch, setField, goNext, goBack, goTo } = wizard;
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
  };

  return (
    <AppShell
      currentView={appState.view}
      hasActiveCourse={appState.activeCourseId !== null}
      onNavigate={navigate}
    >
      {appState.view === "setup" && renderSetup()}
      {appState.view === "dashboard" && (
        <Dashboard onOpenCourse={openCourse} />
      )}
      {appState.view === "workspace" && appState.activeCourseId && (
        <WorkspacePage
          courseId={appState.activeCourseId}
          onBack={() => navigate("dashboard")}
        />
      )}
    </AppShell>
  );
}
