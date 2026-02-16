import { useState, useEffect, useRef, useCallback } from "react";
import type { Engine, EngineRunResult } from "../../types";
import { listEngines, runEngine, getEngineStatus } from "../../api/engines";

export function EnginePanel() {
  const [engines, setEngines] = useState<Engine[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningEngine, setRunningEngine] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<EngineRunResult | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval>>();

  const loadEngines = useCallback(async () => {
    try {
      const list = await listEngines();
      setEngines(list);
    } catch {
      setEngines([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEngines();
  }, [loadEngines]);

  // Poll status while engine is running
  useEffect(() => {
    if (!runningEngine) return;

    pollRef.current = setInterval(async () => {
      try {
        const status = await getEngineStatus(runningEngine);
        if (status.message) {
          setLogs((prev) => {
            const last = prev[prev.length - 1];
            if (last !== status.message) {
              return [...prev, status.message!];
            }
            return prev;
          });
        }
        if (status.status !== "running") {
          setRunningEngine(null);
          loadEngines();
        }
      } catch {
        // Ignore poll errors
      }
    }, 2000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [runningEngine, loadEngines]);

  const handleRun = async (engine: Engine) => {
    setRunningEngine(engine.name);
    setLastResult(null);
    setLogs([`Starting ${engine.name}...`]);

    try {
      const result = await runEngine({ name: engine.name });
      setLastResult(result);
      setLogs((prev) => [
        ...prev,
        `Completed: ${result.message} (${result.duration_ms}ms)`,
      ]);
      setRunningEngine(null);
      loadEngines();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Engine run failed";
      setLogs((prev) => [...prev, `Error: ${msg}`]);
      setRunningEngine(null);
      loadEngines();
    }
  };

  const statusColor = (status: Engine["status"]) => {
    switch (status) {
      case "idle":
        return "bg-content-tertiary text-content-muted";
      case "running":
        return "bg-blue-900/30 text-blue-400";
      case "error":
        return "bg-red-900/30 text-red-400";
    }
  };

  const statusDot = (status: Engine["status"]) => {
    switch (status) {
      case "idle":
        return "bg-gray-500";
      case "running":
        return "bg-blue-500 animate-pulse";
      case "error":
        return "bg-red-500";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-content">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-content">
      {/* Header */}
      <div className="px-8 pt-8 pb-4">
        <h1 className="text-2xl font-bold text-content-text">Engines</h1>
        <p className="text-sm text-content-muted mt-0.5">
          Background processing engines for your knowledge base
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-8 pb-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
          {engines.map((engine) => (
            <div
              key={engine.name}
              className="border border-content-border rounded-lg p-5 bg-content-secondary hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div className={`w-2.5 h-2.5 rounded-full ${statusDot(engine.status)}`} />
                  <h3 className="text-sm font-semibold text-content-text">
                    {engine.name}
                  </h3>
                </div>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${statusColor(engine.status)}`}
                >
                  {engine.status}
                </span>
              </div>

              <p className="text-xs text-content-muted mb-4 leading-relaxed">
                {engine.description}
              </p>

              <div className="flex items-center justify-between">
                <div className="text-[11px] text-content-faint">
                  {engine.last_run
                    ? `Last run: ${new Date(engine.last_run).toLocaleString()}`
                    : "Never run"}
                </div>
                <button
                  onClick={() => handleRun(engine)}
                  disabled={
                    engine.status === "running" || runningEngine !== null
                  }
                  className="px-3 py-1.5 text-xs bg-accent text-white rounded-md hover:bg-accent-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {engine.status === "running" || runningEngine === engine.name
                    ? "Running..."
                    : "Run"}
                </button>
              </div>
            </div>
          ))}

          {engines.length === 0 && (
            <div className="col-span-2 text-center py-16">
              <div className="text-4xl mb-3 opacity-30">{"\u2699"}</div>
              <p className="text-content-muted text-sm">No engines available</p>
              <p className="text-content-faint text-xs mt-1">
                Engines process your knowledge base in the background.
              </p>
            </div>
          )}
        </div>

        {/* Log output */}
        {logs.length > 0 && (
          <div className="border border-content-border rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 bg-content-secondary border-b border-content-border">
              <span className="text-xs font-semibold text-content-muted">
                Engine Log
              </span>
              <button
                onClick={() => setLogs([])}
                className="text-[10px] text-content-faint hover:text-content-muted transition-colors"
              >
                Clear
              </button>
            </div>
            <div className="bg-[#1a1a1a] p-4 max-h-60 overflow-y-auto font-mono text-xs text-content-text space-y-1">
              {logs.map((log, i) => (
                <div key={i} className="flex gap-2">
                  <span className="text-content-faint select-none shrink-0">
                    {String(i + 1).padStart(3, " ")}
                  </span>
                  <span
                    className={
                      log.startsWith("Error")
                        ? "text-red-400"
                        : log.startsWith("Completed")
                          ? "text-green-400"
                          : ""
                    }
                  >
                    {log}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Last result */}
        {lastResult && (
          <div
            className={`mt-4 p-4 rounded-lg border animate-fade-in ${
              lastResult.status === "success"
                ? "bg-green-900/20 border-green-800/40"
                : "bg-red-900/20 border-red-800/40"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span
                className={`text-sm ${
                  lastResult.status === "success"
                    ? "text-green-400"
                    : "text-red-400"
                }`}
              >
                {lastResult.status === "success" ? "\u2713" : "\u2717"}
              </span>
              <span
                className={`text-sm font-medium ${
                  lastResult.status === "success"
                    ? "text-green-300"
                    : "text-red-300"
                }`}
              >
                {lastResult.name}
              </span>
            </div>
            <p
              className={`text-xs ${
                lastResult.status === "success"
                  ? "text-green-400"
                  : "text-red-400"
              }`}
            >
              {lastResult.message}
            </p>
            <p className="text-[10px] text-content-faint mt-1">
              Duration: {lastResult.duration_ms}ms
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
