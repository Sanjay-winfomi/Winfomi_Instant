import { useState } from "react";
import "./LandingScreen.css";

const EXAMPLES = [
  "Automate customer support ticket routing",
  "Identify customers at risk of leaving",
  "Process invoices and flag suspicious ones",
  "Analyze customer reviews for declining sentiment",
  "Monitor inventory and alert suppliers on low stock",
];

interface Props {
  onSubmit: (text: string) => void;
  errorMessage: string | null;
  initialText: string;
}

export default function LandingScreen({ onSubmit, errorMessage, initialText }: Props) {
  const [text, setText] = useState(initialText);
  const [touched, setTouched] = useState(false);

  const trimmed = text.trim();
  const tooShort = touched && trimmed.length > 0 && trimmed.length < 5;
  const canSubmit = trimmed.length >= 5;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!canSubmit) return;
    onSubmit(trimmed);
  };

  return (
    <section className="landing">
      <div className="landing-copy">
        <h1>
          Instead of booking a demo, <span className="gradient-text">describe your problem</span> and get a working
          AI prototype instantly.
        </h1>
        <p>
          Type any business process you want to automate. Four AI agents — Requirement Analyzer, Planner, Critic, and
          Executor — will design, validate, and run a real simulated workflow in seconds.
        </p>
      </div>

      <form className="landing-form" onSubmit={handleSubmit}>
        <label htmlFor="problem-input" className="sr-only">
          What do you want to automate?
        </label>
        <textarea
          id="problem-input"
          placeholder="e.g. I want an AI agent that checks inventory and alerts suppliers when stock falls below 20%..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onBlur={() => setTouched(true)}
          rows={5}
          maxLength={2000}
          aria-invalid={tooShort}
          aria-describedby={tooShort ? "input-error" : undefined}
        />
        <div className="landing-form-row">
          <div className="landing-form-hint" id="input-error" role={tooShort ? "alert" : undefined}>
            {tooShort && <span className="error-text">Please describe your problem in a bit more detail.</span>}
            {errorMessage && <span className="error-text">{errorMessage}</span>}
          </div>
          <button type="submit" className="btn-primary" disabled={!canSubmit}>
            Build My AI Demo
          </button>
        </div>
      </form>

      <div className="landing-examples">
        <span className="landing-examples-label">Try an example</span>
        <div className="chip-row">
          {EXAMPLES.map((ex) => (
            <button type="button" key={ex} className="chip" onClick={() => setText(ex)}>
              {ex}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
