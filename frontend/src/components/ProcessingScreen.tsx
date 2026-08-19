import { useEffect, useState } from "react";
import "./ProcessingScreen.css";

const STEPS = [
  "Analyzing your requirement...",
  "Designing workflow...",
  "Validating workflow...",
  "Running agent...",
];

const STEP_INTERVAL_MS = 850;

export default function ProcessingScreen() {
  const [completed, setCompleted] = useState(0);

  useEffect(() => {
    if (completed >= STEPS.length) return;
    const timer = setTimeout(() => setCompleted((c) => c + 1), STEP_INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [completed]);

  return (
    <section className="processing">
      <div className="processing-card">
        <div className="processing-spinner" aria-hidden="true" />
        <h2>Building your AI prototype</h2>
        <ul className="processing-steps">
          {STEPS.map((label, i) => {
            const state = i < completed ? "done" : i === completed ? "active" : "pending";
            return (
              <li key={label} className={`processing-step processing-step--${state}`}>
                <span className="processing-step-icon">{state === "done" ? "✓" : state === "active" ? "⟳" : "○"}</span>
                <span>{label}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
