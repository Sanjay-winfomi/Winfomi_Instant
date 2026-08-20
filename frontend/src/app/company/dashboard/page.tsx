"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getDashboard } from "@/services/companyApi";
import type { DashboardKpis } from "@/types/api";

export default function CompanyDashboardPage() {
  const [data, setData] = useState<DashboardKpis | null>(null);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => undefined);
  }, []);

  if (!data) return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;

  const kpis = [
    { label: "Total leads", value: data.total_leads },
    { label: "New leads", value: data.new_leads },
    { label: "Total demos", value: data.total_demos },
    { label: "Active demos", value: data.active_demos },
    { label: "Demo success rate", value: `${data.demo_success_rate}%` },
    { label: "Avg. critic score", value: data.average_critic_score.toFixed(1) },
    { label: "Avg. generation time", value: `${Math.round(data.average_generation_time_ms)}ms` },
    { label: "Qualified lead rate", value: `${data.qualified_lead_rate}%` },
  ];

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <div className="kpi-grid">
        {kpis.map((k) => (
          <div className="kpi-card" key={k.label}>
            <span className="kpi-card-label">{k.label}</span>
            <span className="kpi-card-value">{k.value}</span>
          </div>
        ))}
      </div>

      <div className="company-grid-2">
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th colSpan={3}>Recent leads</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_leads.map((l) => (
                <tr key={l.id}>
                  <td>{l.email}</td>
                  <td>
                    <span className={`status-badge status-badge--${l.status}`}>{l.status}</span>
                  </td>
                  <td>{l.score}</td>
                </tr>
              ))}
              {data.recent_leads.length === 0 && (
                <tr>
                  <td>No leads yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th colSpan={2}>Recent demos</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_demos.map((d) => (
                <tr key={d.session_id}>
                  <td>
                    <Link href={`/company/demos/${d.session_id}`}>{d.title ?? d.session_id}</Link>
                  </td>
                  <td>{d.outcome}</td>
                </tr>
              ))}
              {data.recent_demos.length === 0 && (
                <tr>
                  <td>No demos yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
