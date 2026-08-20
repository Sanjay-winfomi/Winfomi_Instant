"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, getCompanyToken, login } from "@/services/companyApi";

export default function CompanyLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (getCompanyToken()) router.replace("/company/dashboard");
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email.trim(), password);
      router.push("/company/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not log in. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
      <div className="landing-console" style={{ width: 360 }}>
        <div className="sidebar-logo" style={{ marginBottom: 18 }}>
          <span className="sidebar-logo-mark">◈</span>
          <span className="sidebar-logo-text">
            WINFOMI
            <br />
            Instant AI
          </span>
        </div>
        <h2 style={{ margin: "0 0 18px", fontSize: "1.15rem" }}>Company sign in</h2>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus
            style={{ padding: "11px 14px", borderRadius: 10, border: "1px solid var(--card-border)", background: "var(--surface-alt)" }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ padding: "11px 14px", borderRadius: 10, border: "1px solid var(--card-border)", background: "var(--surface-alt)" }}
          />
          {error && <span className="error-text">{error}</span>}
          <button type="submit" className="btn-primary" disabled={submitting || !email || !password}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
