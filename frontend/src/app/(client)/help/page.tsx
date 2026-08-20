export default function HelpPage() {
  return (
    <div className="panel" style={{ maxWidth: 640 }}>
      <span className="panel-title">Help</span>
      <div style={{ display: "flex", flexDirection: "column", gap: 14, fontSize: "0.9rem", lineHeight: 1.6 }}>
        <div>
          <strong>How does this work?</strong>
          <p style={{ color: "var(--text-muted)", margin: "4px 0 0" }}>
            Describe a business problem in plain English on the Create Demo page. AI agents understand the
            requirement, design a workflow from a safe set of tools, validate it, and run it against sample data to
            produce an interactive mini web app.
          </p>
        </div>
        <div>
          <strong>Can I change the result?</strong>
          <p style={{ color: "var(--text-muted)", margin: "4px 0 0" }}>
            Yes — open a demo from &quot;My Demo&quot; and use &quot;Modify this solution&quot; to describe a change
            in natural language.
          </p>
        </div>
        <div>
          <strong>What if I want the real thing built?</strong>
          <p style={{ color: "var(--text-muted)", margin: "4px 0 0" }}>
            Use &quot;Request Full Solution&quot; on any demo and our team will follow up.
          </p>
        </div>
      </div>
    </div>
  );
}
