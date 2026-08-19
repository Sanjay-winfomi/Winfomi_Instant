import type { WorkflowBlueprint } from "../types/api";
import "./BlueprintView.css";

export default function BlueprintView({ blueprint }: { blueprint: WorkflowBlueprint }) {
  return (
    <div className="blueprint">
      <div className="blueprint-banner">
        <span className="blueprint-banner-icon">◈</span>
        <div>
          <strong>Your requirement is understood, but this capability needs a live data connection.</strong>
          <p>{blueprint.integration_note}</p>
        </div>
      </div>

      <div className="blueprint-grid">
        <div>
          <span className="blueprint-section-label">Expected output</span>
          <p>{blueprint.expected_output_description}</p>
        </div>
        <div>
          <span className="blueprint-section-label">Tools this workflow would use</span>
          <div className="blueprint-tools">
            {blueprint.tools_required.map((t) => (
              <span key={t} className="blueprint-tool-pill">
                {t.replaceAll("_", " ")}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
