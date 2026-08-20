"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { listDemos } from "@/services/companyApi";
import type { DemoListItem } from "@/types/api";

const PAGE_SIZE = 20;

export default function DemosPage() {
  const router = useRouter();
  const [demos, setDemos] = useState<DemoListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [outcome, setOutcome] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    listDemos({ outcome: outcome || undefined, search: search || undefined, page, page_size: PAGE_SIZE })
      .then((res) => {
        setDemos(res.items);
        setTotal(res.total);
      })
      .catch(() => undefined);
  }, [outcome, search, page]);

  return (
    <>
      <h1 className="page-title">Demos</h1>
      <div className="filter-bar">
        <input
          placeholder="Search requirement text…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <select
          value={outcome}
          onChange={(e) => {
            setOutcome(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All outcomes</option>
          <option value="executed">Executed</option>
          <option value="blueprint">Blueprint</option>
          <option value="error">Error</option>
        </select>
      </div>

      <div className="data-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Demo</th>
              <th>Client</th>
              <th>Outcome</th>
              <th>Critic score</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {demos.map((d) => (
              <tr key={d.session_id} onClick={() => router.push(`/company/demos/${d.session_id}`)}>
                <td>{d.title ?? d.session_id}</td>
                <td>{d.lead_email ?? "—"}</td>
                <td>{d.outcome}</td>
                <td>{d.critic_score ?? "—"}</td>
                <td>{new Date(d.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {demos.length === 0 && (
              <tr>
                <td colSpan={5} style={{ color: "var(--text-muted)" }}>
                  No demos found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination-row">
        <span>
          {total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1}-{Math.min(page * PAGE_SIZE, total)} of {total}
        </span>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" className="btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Prev
          </button>
          <button type="button" className="btn-secondary" disabled={page * PAGE_SIZE >= total} onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      </div>
    </>
  );
}
