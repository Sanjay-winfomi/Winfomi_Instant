"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, startClientSession } from "@/services/clientApi";

export default function StartPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [touched, setTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmed = email.trim();
  const isValid = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(trimmed);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!isValid || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await startClientSession(trimmed);
      router.push("/create");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start your session. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section style={{ maxWidth: 440, margin: "10vh auto 0" }}>
      <div className="landing-console">
        <h2 style={{ margin: "0 0 8px", fontSize: "1.3rem" }}>Enter your email to get started</h2>
        <p style={{ margin: "0 0 20px", color: "var(--text-muted)", fontSize: "0.9rem" }}>
          We&apos;ll use this to save your demo so you can come back to it.
        </p>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onBlur={() => setTouched(true)}
            placeholder="you@company.com"
            autoFocus
            style={{
              padding: "12px 16px",
              borderRadius: 999,
              border: "1px solid var(--card-border)",
              background: "var(--surface-alt)",
              fontSize: "0.95rem",
            }}
          />
          {touched && !isValid && trimmed.length > 0 && <span className="error-text">Enter a valid email address.</span>}
          {error && <span className="error-text">{error}</span>}
          <button type="submit" className="btn-primary" disabled={!isValid || submitting}>
            {submitting ? "Starting…" : "Start Building"}
          </button>
        </form>
      </div>
    </section>
  );
}
