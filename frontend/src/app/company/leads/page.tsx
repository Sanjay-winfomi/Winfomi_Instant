"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { listLeads } from "@/services/companyApi";
import type { Lead } from "@/types/api";

const STATUSES = ["NEW", "ENGAGED", "QUALIFIED", "CONTACTED", "CONVERTED", "CLOSED"];
const PAGE_SIZE = 20;

export default function LeadsPage() {
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("-created_at");

  useEffect(() => {
    listLeads({ status: status || undefined, search: search || undefined, sort, page, page_size: PAGE_SIZE })
      .then((res) => {
        setLeads(res.items);
        setTotal(res.total);
      })
      .catch(() => undefined);
  }, [status, search, sort, page]);

  return (
    <>
      <h1 className="page-title">Leads</h1>
      <div className="filter-bar">
        <input
          placeholder="Search email…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="-created_at">Newest first</option>
          <option value="created_at">Oldest first</option>
          <option value="-score">Highest score</option>
          <option value="email">Email A-Z</option>
        </select>
      </div>

      <div className="data-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Score</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((l) => (
              <tr key={l.id} onClick={() => router.push(`/company/leads/${l.id}`)}>
                <td>{l.email}</td>
                <td>
                  <span className={`status-badge status-badge--${l.status}`}>{l.status}</span>
                </td>
                <td>{l.priority}</td>
                <td>{l.score}</td>
                <td>{new Date(l.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {leads.length === 0 && (
              <tr>
                <td colSpan={5} style={{ color: "var(--text-muted)" }}>
                  No leads found.
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
          <button
            type="button"
            className="btn-secondary"
            disabled={page * PAGE_SIZE >= total}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </>
  );
}
