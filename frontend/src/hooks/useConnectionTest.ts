import { useState, useCallback } from "react";
import type { ConnectionResult } from "../types/setup";

type Status = "idle" | "loading" | "success" | "error";

export function useConnectionTest(
  testFn: () => Promise<ConnectionResult>,
) {
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<ConnectionResult | null>(null);

  const run = useCallback(async () => {
    setStatus("loading");
    setResult(null);
    try {
      const res = await testFn();
      setResult(res);
      setStatus(res.ok ? "success" : "error");
    } catch (err) {
      setResult({
        ok: false,
        service: "unknown",
        message: err instanceof Error ? err.message : "Connection failed",
      });
      setStatus("error");
    }
  }, [testFn]);

  const reset = useCallback(() => {
    setStatus("idle");
    setResult(null);
  }, []);

  return { status, result, run, reset };
}
