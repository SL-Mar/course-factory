import { StepNavigation } from "../shared/StepNavigation";

interface WelcomeStepProps {
  onNext: () => void;
}

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600/20 text-2xl font-bold text-indigo-400 ring-1 ring-indigo-500/30">
          CF
        </div>
        <h1 className="text-3xl font-bold text-gray-100">
          Welcome to Course Factory
        </h1>
        <p className="mx-auto max-w-md text-gray-400">
          Let's configure your environment. You'll set up your license key,
          connect to LLM providers, and verify service connections.
        </p>
      </div>

      <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-300">
          What you'll configure:
        </h2>
        <div className="grid gap-3">
          {[
            {
              title: "License Key",
              desc: "Activate your Course Factory license",
            },
            {
              title: "LLM Providers",
              desc: "Ollama, Anthropic, and OpenAI connections",
            },
            {
              title: "Services",
              desc: "Database, vector store, and cache",
            },
            {
              title: "Notifications",
              desc: "Telegram webhook for status updates",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="flex items-start gap-3 rounded-lg border border-surface-border bg-surface p-3"
            >
              <span className="mt-0.5 h-2 w-2 flex-shrink-0 rounded-full bg-indigo-500" />
              <div>
                <p className="text-sm font-medium text-gray-200">
                  {item.title}
                </p>
                <p className="text-xs text-gray-500">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <StepNavigation
        onNext={onNext}
        nextLabel="Get Started"
        showBack={false}
      />
    </div>
  );
}
