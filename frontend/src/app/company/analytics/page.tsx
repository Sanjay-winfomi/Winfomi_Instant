"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getAnalytics } from "@/services/companyApi";
import type { AnalyticsSummary } from "@/types/api";

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    getAnalytics()
      .then(setData)
      .catch(() => undefined);
  }, []);

  if (!data) return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;

  return (
    <>
      <h1 className="page-title">Analytics</h1>

      <div className="kpi-grid">
        <div className="kpi-card">
          <span className="kpi-card-label">Workflow success rate</span>
          <span className="kpi-card-value">{data.workflow_success_rate}%</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-card-label">Avg. fields per requirement</span>
          <span className="kpi-card-value">{data.average_requirement_fields}</span>
        </div>
      </div>

      <div className="company-grid-2">
        <div className="panel">
          <span className="panel-title">Lead funnel</span>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.funnel} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border)" />
              <XAxis type="number" allowDecimals={false} />
              <YAxis type="category" dataKey="stage" width={130} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="var(--accent-1)" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <span className="panel-title">Leads &amp; demos over time</span>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data.trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border)" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="leads" stroke="var(--chip-purple)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="demos" stroke="var(--accent-1)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
