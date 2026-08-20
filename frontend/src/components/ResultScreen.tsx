import type { DemoResult } from "../types/api";
import BlueprintView from "./BlueprintView";
import CriticScoreCard from "./CriticScoreCard";
import DynamicMiniAppRenderer from "./DynamicMiniAppRenderer";
import ExecutionTrace from "./ExecutionTrace";
import "./ResultScreen.css";
import WorkflowDiagram from "./WorkflowDiagram";

interface Props {
  result: DemoResult;
  onReset: () => void;
  /** True from the company portal's demo preview (spec §34) - same renderer, but
   * interactive actions are disabled since there's no client lead session here. */
  readOnly?: boolean;
}

export default function ResultScreen({ result, onReset, readOnly = false }: Props) {
  if (result.outcome === "error" || !result.requirement) {
    return (
      <section className="result-screen">
        <div className="result-error">
          <h2>Something went wrong</h2>
          <p>{result.error ?? "The pipeline could not complete. Please try again."}</p>
          <button type="button" className="btn-primary" onClick={onReset}>
            Try Again
          </button>
        </div>
      </section>
    );
  }

  const displaySteps = result.outcome === "blueprint" ? result.blueprint?.proposed_workflow ?? [] : result.workflow?.steps ?? [];

  return (
    <section className="result-screen">
      <div className="result-header">
        <div>
          <span className={`mode-badge mode-badge--${result.mode}`}>
            {result.mode === "live" ? "Live AI mode" : "Demo fallback mode"}
          </span>
          <h2>{result.requirement.goal}</h2>
        </div>
        <button type="button" className="btn-secondary" onClick={onReset}>
          Try Another Scenario
        </button>
      </div>

      <div className="result-grid">
        <div className="result-main">
          <div className="panel">
            <span className="panel-title">Generated workflow</span>
            <WorkflowDiagram steps={displaySteps} stepResults={result.execution?.step_results} />
          </div>

          {result.outcome === "executed" && result.ui_schema && (
            <div className="panel">
              <span className="panel-title">Try it live</span>
              <DynamicMiniAppRenderer sessionId={result.session_id} schema={result.ui_schema} readOnly={readOnly} />
            </div>
          )}

          {result.outcome === "executed" && result.execution && (
            <div className="panel">
              <span className="panel-title">Execution trace (full batch run)</span>
              <ExecutionTrace steps={result.execution.step_results} />
            </div>
          )}

          {result.outcome === "blueprint" && result.blueprint && (
            <div className="panel">
              <span className="panel-title">Workflow Blueprint</span>
              <BlueprintView blueprint={result.blueprint} />
            </div>
          )}

          {result.rejected_steps.length > 0 && (
            <div className="panel panel--muted">
              <span className="panel-title">Safety layer: blocked steps</span>
              <ul className="rejected-list">
                {result.rejected_steps.map((r, i) => (
                  <li key={i}>
                    {r.tool ? <strong>{r.tool}</strong> : <strong>Workflow limit</strong>} — {r.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="result-side">
          {result.critic && <CriticScoreCard critic={result.critic} history={result.critic_history} />}

          <div className="panel">
            <span className="panel-title">Structured requirement</span>
            <dl className="requirement-list">
              <dt>Goal</dt>
              <dd>{result.requirement.goal}</dd>
              <dt>Input</dt>
              <dd>{result.requirement.input}</dd>
              {result.requirement.condition && (
                <>
                  <dt>Condition</dt>
                  <dd>{result.requirement.condition}</dd>
                </>
              )}
              <dt>Action</dt>
              <dd>{result.requirement.action}</dd>
              <dt>Expected output</dt>
              <dd>{result.requirement.expected_output}</dd>
            </dl>
          </div>
        </div>
      </div>
    </section>
  );
}
