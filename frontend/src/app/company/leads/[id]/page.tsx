"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { addLeadNote, getLead, updateLead } from "@/services/companyApi";
import type { LeadDetail } from "@/types/api";

const STATUSES = ["NEW", "ENGAGED", "QUALIFIED", "CONTACTED", "CONVERTED", "CLOSED"];
const PRIORITIES = ["low", "normal", "high"];

export default function LeadDetailPage() {
  const params = useParams<{ id: string }>();
  const leadId = Number(params.id);
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const refresh = () => getLead(leadId).then(setLead).catch(() => undefined);

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leadId]);

  if (!lead) return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;

  const handleStatusChange = async (status: string) => {
    await updateLead(leadId, { status });
    refresh();
  };

  const handlePriorityChange = async (priority: string) => {
    await updateLead(leadId, { priority });
    refresh();
  };

  const handleAddNote = async () => {
    if (!note.trim()) return;
    setSaving(true);
    try {
      await addLeadNote(leadId, note.trim());
      setNote("");
      refresh();
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <h1 className="page-title">{lead.email}</h1>

      <div className="company-grid-2">
        <div className="panel">
          <span className="panel-title">Lead details</span>
          <div style={{ display: "flex", gap: 20, flexWrap: "wrap", marginBottom: 16 }}>
            <label>
              Status
              <br />
              <select value={lead.status} onChange={(e) => handleStatusChange(e.target.value)}>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Priority
              <br />
              <select value={lead.priority} onChange={(e) => handlePriorityChange(e.target.value)}>
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </label>
            <div>
              Lead score
              <br />
              <strong style={{ fontSize: "1.2rem" }}>{lead.score}</strong>
            </div>
          </div>

          <span className="panel-title">Activity</span>
          <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6, fontSize: "0.85rem" }}>
            {lead.events.map((e, i) => (
              <li key={i} style={{ color: "var(--text-muted)" }}>
                <strong style={{ color: "var(--text-primary)" }}>{e.event_type}</strong> — {new Date(e.created_at).toLocaleString()}
              </li>
            ))}
            {lead.events.length === 0 && <li style={{ color: "var(--text-muted)" }}>No activity yet.</li>}
          </ul>
        </div>

        <div className="panel">
          <span className="panel-title">Demos</span>
          <ul style={{ margin: "0 0 20px", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
            {lead.demos.map((d) => (
              <li key={d.session_id}>
                <Link href={`/company/demos/${d.session_id}`}>{d.title ?? d.session_id}</Link>
                <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}> — {d.outcome}</span>
              </li>
            ))}
            {lead.demos.length === 0 && <li style={{ color: "var(--text-muted)" }}>No demos yet.</li>}
          </ul>

          <span className="panel-title">Internal notes (never shown to the client)</span>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 14 }}>
            {lead.notes.map((n) => (
              <div key={n.id} style={{ padding: "8px 12px", background: "var(--surface-alt)", borderRadius: 10, fontSize: "0.85rem" }}>
                <div>{n.note}</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", marginTop: 4 }}>
                  {new Date(n.created_at).toLocaleString()}
                </div>
              </div>
            ))}
            {lead.notes.length === 0 && <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No notes yet.</p>}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              style={{ flex: 1, padding: "9px 14px", borderRadius: 10, border: "1px solid var(--card-border)" }}
              placeholder="Add a note…"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            <button type="button" className="btn-secondary" onClick={handleAddNote} disabled={saving || !note.trim()}>
              Add
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
