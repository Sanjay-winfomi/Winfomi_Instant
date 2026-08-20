"use client";

import { useEffect, useMemo, useState } from "react";
import { getActionsLog, logEvent, runRecord, takeAction } from "@/services/clientApi";
import type { ActionLogEntry, ExecutionResult, UiResult, UiSchema } from "@/types/api";
import ExecutionTrace from "./ExecutionTrace";
import "./DynamicMiniAppRenderer.css";

interface Props {
  sessionId: string;
  schema: UiSchema;
  /** True when rendered from the company portal preview (spec §34) - the exact same
   * schema/data render, but Run/Action buttons are disabled since there's no client
   * lead session to attribute the interaction to. */
  readOnly?: boolean;
}

function SchemaTable({ result, selectedId, onSelect }: { result: UiResult; selectedId: string; onSelect: (id: string) => void }) {
  const columns = result.columns ?? [];
  const rows = (result.rows ?? []) as Record<string, unknown>[];
  return (
    <div className="dyn-table-wrap">
      <table className="dyn-table">
        <thead>
          <tr>
            <th />
            {columns.map((c) => (
              <th key={c}>{c.replaceAll("_", " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const id = String(row.id);
            const isSelected = id === selectedId;
            return (
              <tr key={id} className={isSelected ? "is-selected" : ""} onClick={() => onSelect(id)}>
                <td>
                  <input type="radio" checked={isSelected} onChange={() => onSelect(id)} aria-label={`Select ${id}`} />
                </td>
                {columns.map((c) => (
                  <td key={c}>{String(row[c] ?? "—")}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function SchemaResultCard({ result }: { result: UiResult }) {
  const content = result.content;
  return (
    <div className="dyn-card">
      <span className="dyn-card-title">{result.title}</span>
      {content && typeof content === "object" ? (
        <pre className="dyn-card-body">{JSON.stringify(content, null, 2)}</pre>
      ) : (
        <p className="dyn-card-body">{String(content ?? "—")}</p>
      )}
    </div>
  );
}

function SchemaStatus({ result }: { result: UiResult }) {
  const value = String(result.content ?? "pending");
  return (
    <div className="dyn-status">
      <span className="dyn-status-title">{result.title}</span>
      <span className={`dyn-status-badge dyn-status-badge--${value}`}>{value.replaceAll("_", " ")}</span>
    </div>
  );
}

export default function DynamicMiniAppRenderer({ sessionId, schema, readOnly = false }: Props) {
  const tableResult = useMemo(() => schema.results.find((r) => r.type === "table"), [schema.results]);
  const cardResults = schema.results.filter((r) => r.type === "card");
  const statusResults = schema.results.filter((r) => r.type === "status");
  const fieldInputs = schema.inputs.filter((i) => i.type !== "record_picker");

  const firstRowId = tableResult?.rows?.[0] ? String(tableResult.rows[0].id) : "";
  const [selectedId, setSelectedId] = useState(firstRowId);
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

  const selectedRow = tableResult?.rows?.find((r) => String(r.id) === selectedId);

  const handleRun = async () => {
    if (!selectedId) return;
    setRunning(true);
    setRunError(null);
    setExecution(null);
    try {
      const result = await runRecord(sessionId, selectedId);
      setExecution(result);
      logEvent("MINI_APP_INTERACTION", sessionId, { kind: "run", record_id: selectedId });
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
      // silently ignore - the button re-enables and the customer can retry
    } finally {
      setActionPending(null);
    }
  };

  const recordActionsTaken = log.filter((l) => l.record_id === selectedId);

  return (
    <div className="dyn-app">
      <div className="dyn-app-header">
        <h3>{schema.app.title}</h3>
        {schema.app.description && <p>{schema.app.description}</p>}
      </div>

      {tableResult && (
        <div className="dyn-section">
          <span className="dyn-section-label">{tableResult.title} — pick one to run the workflow against</span>
          <SchemaTable result={tableResult} selectedId={selectedId} onSelect={setSelectedId} />
        </div>
      )}

      {selectedRow && fieldInputs.length > 0 && (
        <div className="dyn-section">
          <span className="dyn-section-label">Selected record</span>
          <div className="dyn-fields-grid">
            {fieldInputs.map((input) => (
              <div key={input.id} className="dyn-field">
                <span className="dyn-field-label">{input.label}</span>
                <span className="dyn-field-value">{String(selectedRow[input.field ?? ""] ?? "—")}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="dyn-section dyn-actions-row">
        {schema.actions
          .filter((a) => a.type === "run")
          .map((a) => (
            <button key={a.id} type="button" className="btn-primary" onClick={handleRun} disabled={readOnly || running || !selectedId}>
              {running ? "Running…" : a.label}
            </button>
          ))}
        {schema.actions
          .filter((a) => a.type === "record_action")
          .map((a) => {
            const takenBefore = recordActionsTaken.some((l) => l.action === a.action);
            return (
              <button
                key={a.id}
                type="button"
                className={`btn-secondary ${takenBefore ? "is-done" : ""}`}
                onClick={() => a.action && handleAction(a.action)}
                disabled={readOnly || actionPending === a.action || !selectedId}
              >
                {takenBefore ? "✓ " : ""}
                {actionPending === a.action ? "Saving…" : a.label}
              </button>
            );
          })}
        {readOnly && <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>Preview only — actions run in the client portal.</span>}
      </div>

      {runError && <p className="mini-app-error">{runError}</p>}
      {recordActionsTaken.length > 0 && (
        <p className="mini-app-action-confirm">Recorded: {recordActionsTaken.map((l) => l.action).join(", ")}</p>
      )}

      {execution && (
        <div className="dyn-section">
          <span className="dyn-section-label">Result for {selectedId}</span>
          <ExecutionTrace steps={execution.step_results} />
        </div>
      )}

      {statusResults.length > 0 && (
        <div className="dyn-section dyn-status-row">
          {statusResults.map((r) => (
            <SchemaStatus key={r.id} result={r} />
          ))}
        </div>
      )}

      {cardResults.length > 0 && (
        <div className="dyn-section dyn-cards-grid">
          {cardResults.map((r) => (
            <SchemaResultCard key={r.id} result={r} />
          ))}
        </div>
      )}
    </div>
  );
}
