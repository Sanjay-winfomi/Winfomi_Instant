"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAgentsOverview } from "@/services/companyApi";
import type { AgentsOverview } from "@/types/api";

export default function AgentsPage() {
  const [data, setData] = useState<AgentsOverview | null>(null);

  useEffect(() => {
    getAgentsOverview()
      .then(setData)
      .catch(() => undefined);
  }, []);

  if (!data) return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;

  return (
    <>
      <h1 className="page-title">Agents</h1>

      <div className="kpi-grid">
        {data.agents.map((a) => (
          <Link key={a.agent_name} href={`/company/agents/${a.agent_name}`} className="kpi-card" style={{ textDecoration: "none", color: "inherit" }}>
            <span className="kpi-card-label" style={{ textTransform: "capitalize" }}>
              {a.agent_name} agent
            </span>
            <span className="kpi-card-value">{a.success_rate}%</span>
            <div style={{ marginTop: 8, fontSize: "0.78rem", color: "var(--text-muted)" }}>
              {a.total_executions} runs · {Math.round(a.average_duration_ms)}ms avg ·{" "}
              <span className={`status-badge status-badge--${a.status === "healthy" ? "QUALIFIED" : "CLOSED"}`}>{a.status}</span>
            </div>
          </Link>
        ))}
      </div>

      <div className="panel">
        <span className="panel-title">Critic quality metrics</span>
        <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
          <div>
            <span className="kpi-card-label">Average score</span>
            <div className="kpi-card-value">{data.critic.average_score}</div>
          </div>
          <div>
            <span className="kpi-card-label">Approval rate</span>
            <div className="kpi-card-value">{data.critic.approval_rate}%</div>
          </div>
          <div>
            <span className="kpi-card-label">Retry rate</span>
            <div className="kpi-card-value">{data.critic.retry_rate}%</div>
          </div>
          <div>
            <span className="kpi-card-label">Rejected workflows</span>
            <div className="kpi-card-value">{data.critic.rejected_workflow_count}</div>
          </div>
        </div>
      </div>
    </>
  );
}
