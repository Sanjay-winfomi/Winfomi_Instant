import { useState } from "react";
import type { StepResult } from "../types/api";
import "./ExecutionTrace.css";

function summarizeOutput(output: unknown): string {
  if (output === null || output === undefined) return "—";
  if (Array.isArray(output)) return `${output.length} record(s)`;
  if (typeof output === "object") {
    const obj = output as Record<string, unknown>;
    if ("decision" in obj) return `decision: ${String(obj.decision)}`;
    if ("message" in obj) return String(obj.message);
    if ("title" in obj) return `report: ${String(obj.title)}`;
    return "1 object";
  }
  return String(output);
}

export default function ExecutionTrace({ steps }: { steps: StepResult[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="execution-trace">
      {steps.map((step, i) => {
        const isOpen = openIndex === i;
        return (
          <div key={i} className={`trace-row trace-row--${step.status}`}>
            <button type="button" className="trace-row-header" onClick={() => setOpenIndex(isOpen ? null : i)}>
              <span className="trace-row-index">{i + 1}</span>
              <span className="trace-row-tool">{step.tool.replaceAll("_", " ")}</span>
              <span className="trace-row-summary">{summarizeOutput(step.output)}</span>
              <span className="trace-row-duration">{step.duration_ms}ms</span>
              <span className="trace-row-caret">{isOpen ? "▾" : "▸"}</span>
            </button>
            {isOpen && (
              <pre className="trace-row-detail">
                {step.error ? `Error: ${step.error}` : JSON.stringify(step.output, null, 2)}
              </pre>
            )}
          </div>
        );
      })}
    </div>
  );
}
