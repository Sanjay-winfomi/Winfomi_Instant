import type { BuildStage } from "@/services/clientApi";
import "./ProcessingScreen.css";

const STAGES: { key: BuildStage; label: string }[] = [
  { key: "understanding", label: "Understanding your requirement" },
  { key: "designing", label: "Designing your solution" },
  { key: "validating", label: "Validating your workflow" },
  { key: "preparing", label: "Preparing your demo" },
];

interface Props {
  /** The current real backend stage (spec §14) - never a fake timer. */
  stage: BuildStage | null;
}

export default function ProcessingScreen({ stage }: Props) {
  const activeIndex = stage ? STAGES.findIndex((s) => s.key === stage) : -1;

  return (
    <section className="processing">
      <div className="processing-card">
        <div className="processing-spinner" aria-hidden="true" />
        <h2>Building your AI prototype</h2>
        <ul className="processing-steps">
          {STAGES.map((s, i) => {
            const state = activeIndex < 0 ? "pending" : i < activeIndex ? "done" : i === activeIndex ? "active" : "pending";
            return (
              <li key={s.key} className={`processing-step processing-step--${state}`}>
                <span className="processing-step-icon">{state === "done" ? "✓" : state === "active" ? "⟳" : "○"}</span>
                <span>{s.label}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
