"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getAgentDetail } from "@/services/companyApi";
import type { AgentMetrics } from "@/types/api";

export default function AgentDetailPage() {
  const params = useParams<{ name: string }>();
  const [data, setData] = useState<AgentMetrics | null>(null);

  useEffect(() => {
    getAgentDetail(params.name)
      .then(setData)
      .catch(() => undefined);
  }, [params.name]);

  if (!data) return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;

  return (
    <>
      <h1 className="page-title" style={{ textTransform: "capitalize" }}>
        {data.agent_name} agent
      </h1>

      <div className="kpi-grid">
        <div className="kpi-card">
          <span className="kpi-card-label">Total executions</span>
          <span className="kpi-card-value">{data.total_executions}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-card-label">Success rate</span>
          <span className="kpi-card-value">{data.success_rate}%</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-card-label">Failures</span>
          <span className="kpi-card-value">{data.failure_count}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-card-label">Avg. duration</span>
          <span className="kpi-card-value">{Math.round(data.average_duration_ms)}ms</span>
        </div>
      </div>

      <div className="data-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Session</th>
              <th>Status</th>
              <th>Attempt</th>
              <th>Duration</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_executions.map((e, i) => (
              <tr key={i}>
                <td>{e.session_id}</td>
                <td>
                  <span className={`status-badge status-badge--${e.status === "success" ? "QUALIFIED" : "CLOSED"}`}>{e.status}</span>
                </td>
                <td>{e.attempt}</td>
                <td>{e.duration_ms}ms</td>
                <td>{new Date(e.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {data.recent_executions.length === 0 && (
              <tr>
                <td colSpan={5} style={{ color: "var(--text-muted)" }}>
                  No executions yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
