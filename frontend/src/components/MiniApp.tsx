import { useEffect, useState } from "react";
import { getActionsLog, runRecord, takeAction } from "../services/api";
import type { ActionLogEntry, ExecutionResult, MiniAppInfo } from "../types/api";
import ExecutionTrace from "./ExecutionTrace";
import "./MiniApp.css";

interface Props {
  sessionId: string;
  miniApp: MiniAppInfo;
}

export default function MiniApp({ sessionId, miniApp }: Props) {
  const [selectedId, setSelectedId] = useState(miniApp.records[0]?.id ?? "");
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [execution, setExecution] = useState<ExecutionResult | null>(null);
  const [actionPending, setActionPending] = useState<string | null>(null);
  const [log, setLog] = useState<ActionLogEntry[]>([]);

  useEffect(() => {
    getActionsLog(sessionId)
      .then(setLog)
      .catch(() => undefined);
  }, [sessionId]);

  const handleRun = async () => {
    if (!selectedId) return;
    setRunning(true);
    setRunError(null);
    setExecution(null);
    try {
      const result = await runRecord(sessionId, selectedId);
      setExecution(result);
    } catch {
      setRunError("Could not run the workflow against this record. Please try again.");
    } finally {
      setRunning(false);
    }
  };

  const handleAction = async (action: string) => {
    if (!selectedId) return;
    setActionPending(action);
    try {
      await takeAction(sessionId, selectedId, action);
      const updatedLog = await getActionsLog(sessionId);
      setLog(updatedLog);
    } catch {
      // silently ignore - the action button re-enables and the customer can retry
    } finally {
      setActionPending(null);
    }
  };

  const recordActionsTaken = log.filter((l) => l.record_id === selectedId);

  return (
    <div className="mini-app">
      <div className="mini-app-controls">
        <label className="mini-app-label" htmlFor="record-select">
          Pick a real record to run this workflow against
        </label>
        <div className="mini-app-controls-row">
          <select
            id="record-select"
            value={selectedId}
            onChange={(e) => {
              setSelectedId(e.target.value);
              setExecution(null);
              setRunError(null);
            }}
          >
            {miniApp.records.map((r) => (
              <option key={r.id} value={r.id}>
                {r.id} — {r.label}
              </option>
            ))}
          </select>
          <button type="button" className="btn-primary mini-app-run" onClick={handleRun} disabled={running}>
            {running ? "Running…" : "Run Workflow"}
          </button>
        </div>
      </div>

      {runError && <p className="mini-app-error">{runError}</p>}

      {execution && (
        <div className="mini-app-result">
          <span className="mini-app-result-label">Result for {selectedId}</span>
          <ExecutionTrace steps={execution.step_results} />
        </div>
      )}

      {miniApp.actions.length > 0 && (
        <div className="mini-app-actions">
          <span className="mini-app-label">Take action on this record</span>
          <div className="mini-app-actions-row">
            {miniApp.actions.map((a) => {
              const takenBefore = recordActionsTaken.some((l) => l.action === a.action);
              return (
                <button
                  key={a.action}
                  type="button"
                  className={`btn-secondary mini-app-action-btn ${takenBefore ? "is-done" : ""}`}
                  onClick={() => handleAction(a.action)}
                  disabled={actionPending === a.action}
                >
                  {takenBefore ? "✓ " : ""}
                  {actionPending === a.action ? "Saving…" : a.label}
                </button>
              );
            })}
          </div>
          {recordActionsTaken.length > 0 && (
            <p className="mini-app-action-confirm">
              Recorded in the database: {recordActionsTaken.map((l) => l.action).join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
