import type { CriticResult } from "../types/api";
import "./CriticScoreCard.css";

const LABELS: Record<keyof CriticResult["scores"], string> = {
  requirement_understanding: "Requirement understanding",
  workflow_completeness: "Workflow completeness",
  logical_correctness: "Logical correctness",
  tool_feasibility: "Tool feasibility",
};

interface Props {
  critic: CriticResult;
  history: CriticResult[];
}

export default function CriticScoreCard({ critic, history }: Props) {
  return (
    <div className="critic-card">
      <div className="critic-card-header">
        <div>
          <span className="critic-card-title">Critic score</span>
          <div className="critic-card-score">
            {critic.overall_score.toFixed(1)}
            <span className="critic-card-score-max">/10</span>
          </div>
        </div>
        <span className={`critic-badge ${critic.approved ? "critic-badge--approved" : "critic-badge--rejected"}`}>
          {critic.approved ? "Approved" : "Not approved"}
        </span>
      </div>

      <div className="critic-bars">
        {(Object.keys(LABELS) as (keyof CriticResult["scores"])[]).map((key) => (
          <div className="critic-bar-row" key={key}>
            <span className="critic-bar-label">{LABELS[key]}</span>
            <div className="critic-bar-track">
              <div className="critic-bar-fill" style={{ width: `${(critic.scores[key] / 10) * 100}%` }} />
            </div>
            <span className="critic-bar-value">{critic.scores[key].toFixed(1)}</span>
          </div>
        ))}
      </div>

      {history.length > 1 && (
        <div className="critic-history">
          <span className="critic-history-label">Planner/Critic attempts</span>
          <div className="critic-history-row">
            {history.map((h) => (
              <span key={h.attempt} className={`critic-history-pill ${h.approved ? "is-approved" : ""}`}>
                #{h.attempt}: {h.overall_score.toFixed(1)}
              </span>
            ))}
          </div>
        </div>
      )}

      {critic.feedback.length > 0 && (
        <ul className="critic-feedback">
          {critic.feedback.map((f, i) => (
            <li key={i}>{f}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
