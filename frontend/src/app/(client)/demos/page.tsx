"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getClientToken, listMyDemos } from "@/services/clientApi";
import type { DemoSummary } from "@/types/api";

const OUTCOME_LABEL: Record<string, string> = {
  executed: "Ready",
  blueprint: "Blueprint only",
  error: "Failed",
};

export default function MyDemosPage() {
  const router = useRouter();
  const [demos, setDemos] = useState<DemoSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getClientToken()) {
      router.replace("/start");
      return;
    }
    listMyDemos()
      .then(setDemos)
      .catch(() => setError("Could not load your demos."));
  }, [router]);

  if (error) return <p className="error-text">{error}</p>;
  if (!demos) return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;

  if (demos.length === 0) {
    return (
      <div className="panel" style={{ maxWidth: 560 }}>
        <span className="panel-title">No demos yet</span>
        <p style={{ color: "var(--text-muted)", margin: "10px 0 16px" }}>
          You haven&apos;t built anything yet. Describe a business problem to get started.
        </p>
        <Link href="/create" className="btn-primary">
          Create Demo
        </Link>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 720 }}>
      <h2 style={{ margin: "0 0 4px" }}>My Demos</h2>
      {demos.map((d) => (
        <Link
          key={d.session_id}
          href={`/demo/${d.session_id}`}
          className="panel"
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", textDecoration: "none", color: "inherit" }}
        >
          <div>
            <div style={{ fontWeight: 700 }}>{d.title ?? "Untitled demo"}</div>
            <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
              {new Date(d.updated_at).toLocaleString()}
            </div>
          </div>
          <span className={`mode-badge mode-badge--${d.outcome === "executed" ? "live" : "fallback"}`}>
            {OUTCOME_LABEL[d.outcome] ?? d.outcome}
          </span>
        </Link>
      ))}
    </div>
  );
}
