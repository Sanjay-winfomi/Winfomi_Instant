import { useState } from "react";
import Link from "next/link";
import FileUploadCard from "./FileUploadCard";
import HeroIllustration from "./HeroIllustration";
import "./LandingScreen.css";

const EXAMPLES: { title: string; description: string; prompt: string; chip: "green" | "purple" | "amber" | "teal" }[] = [
  {
    title: "Support ticket routing",
    description: "Classify and route incoming tickets automatically",
    prompt: "Automate customer support ticket routing",
    chip: "green",
  },
  {
    title: "Customer risk alerts",
    description: "Flag customers at risk of leaving and notify sales",
    prompt: "Identify customers at risk of leaving",
    chip: "purple",
  },
  {
    title: "Invoice verification",
    description: "Extract invoice data and flag suspicious ones",
    prompt: "Process invoices and flag suspicious ones",
    chip: "amber",
  },
  {
    title: "Sentiment monitoring",
    description: "Spot declining sentiment in customer reviews",
    prompt: "Analyze customer reviews for declining sentiment",
    chip: "teal",
  },
];

const CHIP_ICON: Record<string, string> = {
  green: "M13 2 3 14h7l-1 8 10-12h-7l1-8Z",
  purple: "M12 2v6M12 16v6M4.9 4.9l4.2 4.2M14.9 14.9l4.2 4.2M2 12h6M16 12h6M4.9 19.1l4.2-4.2M14.9 9.1l4.2-4.2",
  amber: "M12 3v2M12 19v2M5 12H3M21 12h-2M6 6l1.4 1.4M18 18l-1.4-1.4M6 18l1.4-1.4M18 6l-1.4 1.4",
  teal: "M4 12a8 8 0 1 0 16 0 8 8 0 0 0-16 0Zm8-4v4l2.5 2.5",
};

interface Props {
  onSubmit: (text: string) => void;
  onSubmitFile: (file: File, instruction: string) => void;
  errorMessage: string | null;
  initialText: string;
}

export default function LandingScreen({ onSubmit, onSubmitFile, errorMessage, initialText }: Props) {
  const [text, setText] = useState(initialText);
  const [touched, setTouched] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

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
      <div className="landing-hero">
        <div className="landing-copy">
          <h1>
            Describe your problem. Get a working <span className="gradient-text">AI prototype</span> instantly.
          </h1>
          <p>
            Four AI agents — Requirement Analyzer, Planner, Critic, and Executor — design, validate, and run a real
            workflow from your description. No code, no waiting for a sales call.
          </p>
        </div>
        <HeroIllustration />
      </div>

      <form className="landing-console" onSubmit={handleSubmit}>
        <label htmlFor="problem-input" className="landing-console-label">
          What do you want to automate?
        </label>
        <div className="landing-console-body">
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
          <div className="landing-console-footer">
            <div className="landing-console-hint" id="input-error" role={tooShort ? "alert" : undefined}>
              {tooShort && <span className="error-text">Please describe your problem in a bit more detail.</span>}
              {errorMessage && <span className="error-text">{errorMessage}</span>}
            </div>
            <span className="landing-console-count">{trimmed.length}/2000</span>
          </div>
        </div>
        <button type="submit" className="btn-primary landing-console-submit" disabled={!canSubmit}>
          <span className="landing-console-sparkle">✦</span>
          Build My AI Demo
        </button>
      </form>

      <div className="landing-secondary-row">
        <button type="button" className="landing-secondary-link" onClick={() => setShowUpload((v) => !v)}>
          {showUpload ? "Hide file upload" : "Or upload a document instead"}
        </button>
        <Link href="/flowchart" className="landing-secondary-link">
          Build a flowchart manually →
        </Link>
      </div>

      {showUpload && <FileUploadCard onSubmitFile={onSubmitFile} errorMessage={null} />}

      <div className="landing-examples">
        <span className="landing-examples-label">Try an example</span>
        <div className="example-grid">
          {EXAMPLES.map((ex) => (
            <button type="button" key={ex.title} className="example-card" onClick={() => setText(ex.prompt)}>
              <span className={`example-card-chip example-card-chip--${ex.chip}`}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d={CHIP_ICON[ex.chip]} />
                </svg>
              </span>
              <span className="example-card-text">
                <span className="example-card-title">{ex.title}</span>
                <span className="example-card-desc">{ex.description}</span>
              </span>
              <svg className="example-card-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m9 18 6-6-6-6" />
              </svg>
            </button>
          ))}
        </div>
      </div>

      <div className="trust-bar">
        <div className="trust-item">
          <span className="trust-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="m18 16 4-4-4-4M6 8l-4 4 4 4M14.5 4l-5 16" />
            </svg>
          </span>
          <span className="trust-label">No Code Needed</span>
          <span className="trust-desc">Describe your process in plain English — nothing to configure.</span>
        </div>
        <div className="trust-item">
          <span className="trust-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M13 2 3 14h7l-1 8 10-12h-7l1-8Z" />
            </svg>
          </span>
          <span className="trust-label">Instant Prototypes</span>
          <span className="trust-desc">A validated, working workflow in seconds, not a scheduled demo.</span>
        </div>
        <div className="trust-item">
          <span className="trust-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
            </svg>
          </span>
          <span className="trust-label">Secure &amp; Private</span>
          <span className="trust-desc">Every step runs through a validated, deterministic tool registry.</span>
        </div>
      </div>
    </section>
  );
}
