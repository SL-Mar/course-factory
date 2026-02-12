import { useState, useCallback } from "react";
import { StepNavigation } from "../shared/StepNavigation";
import { StatusCard } from "../shared/StatusCard";
import { cn } from "../../utils/cn";
import { validateLicense } from "../../api/setup";
import type { LicenseInfo, WizardState } from "../../types/setup";

interface LicenseStepProps {
  state: WizardState;
  setField: (field: keyof WizardState, value: unknown) => void;
  dispatch: React.Dispatch<{ type: "SET_LICENSE_INFO"; info: LicenseInfo }>;
  onNext: () => void;
  onBack: () => void;
}

export function LicenseStep({
  state,
  setField,
  dispatch,
  onNext,
  onBack,
}: LicenseStepProps) {
  const [validating, setValidating] = useState(false);

  const handleValidate = useCallback(async () => {
    if (!state.license_key.trim()) return;
    setValidating(true);
    try {
      const info = await validateLicense(state.license_key.trim());
      dispatch({ type: "SET_LICENSE_INFO", info });
    } catch {
      dispatch({
        type: "SET_LICENSE_INFO",
        info: {
          valid: false,
          email: "",
          product: "",
          tier: "",
          expiry: "",
          is_expired: false,
          error: "Failed to validate license key.",
        },
      });
    } finally {
      setValidating(false);
    }
  }, [state.license_key, dispatch]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">License Key</h2>
        <p className="mt-1 text-sm text-gray-400">
          Paste your Course Factory license key to activate.
        </p>
      </div>

      <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-4">
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-gray-300">
            License Key
          </label>
          <textarea
            value={state.license_key}
            onChange={(e) => {
              setField("license_key", e.target.value);
              setField("licenseInfo", null);
            }}
            placeholder="Paste your license key here..."
            rows={3}
            className={cn(
              "w-full rounded-lg border border-surface-border bg-surface px-3 py-2.5",
              "font-mono text-sm text-gray-100 placeholder-gray-600",
              "focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500",
              "transition-colors duration-200 resize-none",
            )}
          />
        </div>

        <button
          type="button"
          onClick={handleValidate}
          disabled={!state.license_key.trim() || validating}
          className={cn(
            "rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-200",
            "bg-indigo-600 text-white hover:bg-indigo-500",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          {validating ? (
            <span className="flex items-center gap-2">
              <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Validating...
            </span>
          ) : (
            "Validate Key"
          )}
        </button>

        {state.licenseInfo && (
          <div className="space-y-3">
            {state.licenseInfo.valid ? (
              <>
                <StatusCard
                  ok={!state.licenseInfo.is_expired}
                  message={
                    state.licenseInfo.is_expired
                      ? "License key is valid but expired."
                      : "License key validated successfully."
                  }
                />
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: "Email", value: state.licenseInfo.email },
                    { label: "Product", value: state.licenseInfo.product },
                    { label: "Tier", value: state.licenseInfo.tier },
                    { label: "Expires", value: state.licenseInfo.expiry.split("T")[0] },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="rounded-lg border border-surface-border bg-surface p-3"
                    >
                      <p className="text-xs text-gray-500">{item.label}</p>
                      <p className="text-sm font-medium text-gray-200">
                        {item.value}
                      </p>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <StatusCard
                ok={false}
                message={state.licenseInfo.error || "Invalid license key."}
              />
            )}
          </div>
        )}
      </div>

      <div className="rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-3">
        <p className="text-xs text-yellow-300/80">
          You can skip this step and configure your license key later.
          Some features may be limited without a valid license.
        </p>
      </div>

      <StepNavigation onBack={onBack} onNext={onNext} />
    </div>
  );
}
