"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import ResultScreen from "@/components/ResultScreen";
import { ApiError, getDemo, logEvent, modifyDemo } from "@/services/clientApi";
import type { DemoResult } from "@/types/api";

export default function DemoPage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const sessionId = params.sessionId;

  const [result, setResult] = useState<DemoResult | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [modifyText, setModifyText] = useState("");
  const [modifying, setModifying] = useState(false);
  const [modifyError, setModifyError] = useState<string | null>(null);
  const [requested, setRequested] = useState(false);
  const [contactPhone, setContactPhone] = useState("");

  useEffect(() => {
    if (!sessionId) return;
    getDemo(sessionId)
      .then((r) => {
        setResult(r);
        logEvent("DEMO_OPENED", sessionId);
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not load this demo."));
  }, [sessionId]);

  const handleModify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (modifyText.trim().length < 3 || modifying) return;
    setModifying(true);
    setModifyError(null);
    try {
      const updated = await modifyDemo(sessionId, modifyText.trim());
      setResult(updated);
      setModifyText("");
    } catch (err) {
      setModifyError(err instanceof ApiError ? err.message : "Could not apply that change. Please try again.");
    } finally {
      setModifying(false);
    }
  };

  const handleRequestSolution = () => {
    setRequested(true);
    logEvent("FULL_SOLUTION_REQUESTED", sessionId);
  };

  if (loadError) {
    return (
      <section className="result-screen">
        <div className="result-error">
          <h2>Could not load this demo</h2>
          <p>{loadError}</p>
        </div>
      </section>
    );
  }

  if (!result) {
    return <p style={{ color: "var(--text-muted)" }}>Loading your demo…</p>;
  }

  return (
    <>
      <ResultScreen result={result} onReset={() => router.push("/create")} />

      {result.outcome === "executed" && (
        <div className="panel" style={{ marginTop: 20, maxWidth: 880 }}>
          <span className="panel-title">Modify this solution</span>
          <form onSubmit={handleModify} style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
            <textarea
              value={modifyText}
              onChange={(e) => setModifyText(e.target.value)}
              placeholder="Describe a change, e.g. 'also flag records missing a due date'"
              rows={2}
              maxLength={2000}
              style={{
                flex: 1,
                minWidth: 260,
                padding: "10px 14px",
                borderRadius: 12,
                border: "1px solid var(--card-border)",
                background: "var(--surface-alt)",
                fontFamily: "inherit",
                fontSize: "0.9rem",
              }}
            />
            <button type="submit" className="btn-primary" disabled={modifying || modifyText.trim().length < 3}>
              {modifying ? "Updating…" : "Apply change"}
            </button>
          </form>
          {modifyError && <p className="error-text" style={{ marginTop: 8 }}>{modifyError}</p>}
        </div>
      )}

      {result.outcome === "executed" && (
        <div className="panel" style={{ marginTop: 20, maxWidth: 880 }}>
          <span className="panel-title">Want the full solution?</span>
          {!requested ? (
            <div style={{ marginTop: 10 }}>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", margin: "0 0 12px" }}>
                This is a live prototype. Request the full solution and our team will follow up.
              </p>
              <button type="button" className="btn-primary" onClick={handleRequestSolution}>
                Request Full Solution
              </button>
            </div>
          ) : (
            <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 10, maxWidth: 360 }}>
              <p style={{ color: "var(--success)", fontSize: "0.9rem", margin: 0 }}>
                Thanks — we&apos;ve logged your interest. Optionally leave a phone number for a faster follow-up:
              </p>
              <input
                type="tel"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder="Phone (optional)"
                style={{
                  padding: "10px 14px",
                  borderRadius: 999,
                  border: "1px solid var(--card-border)",
                  background: "var(--surface-alt)",
                }}
              />
              <button
                type="button"
                className="btn-secondary"
                onClick={() => logEvent("FULL_SOLUTION_REQUESTED", sessionId, { phone: contactPhone })}
                disabled={!contactPhone.trim()}
              >
                Submit
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
