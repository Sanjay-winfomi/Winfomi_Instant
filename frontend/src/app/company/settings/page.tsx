"use client";

import { useEffect, useState } from "react";
import { getSettings, updateSettings } from "@/services/companyApi";
import type { CompanySettings } from "@/types/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<CompanySettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch(() => undefined);
  }, []);

  if (!settings) return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;

  const handleChange = (patch: Partial<CompanySettings>) => {
    setSettings({ ...settings, ...patch });
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateSettings(settings);
      setSettings(updated);
      setSaved(true);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <h1 className="page-title">Settings</h1>
      <div className="panel" style={{ maxWidth: 520 }}>
        <span className="panel-title">AI configuration</span>
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <label>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 6 }}>Critic approval threshold (0–10)</div>
            <input
              type="number"
              min={0}
              max={10}
              step={0.1}
              value={settings.critic_approval_threshold}
              onChange={(e) => handleChange({ critic_approval_threshold: Number(e.target.value) })}
              style={{ padding: "9px 14px", borderRadius: 10, border: "1px solid var(--card-border)", width: "100%" }}
            />
            <p style={{ margin: "4px 0 0", fontSize: "0.78rem", color: "var(--text-muted)" }}>
              A generated workflow must score at least this high to be approved and executed.
            </p>
          </label>

          <label>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 6 }}>Max planner retries</div>
            <input
              type="number"
              min={0}
              max={5}
              value={settings.max_planner_retries}
              onChange={(e) => handleChange({ max_planner_retries: Number(e.target.value) })}
              style={{ padding: "9px 14px", borderRadius: 10, border: "1px solid var(--card-border)", width: "100%" }}
            />
            <p style={{ margin: "4px 0 0", fontSize: "0.78rem", color: "var(--text-muted)" }}>
              How many times the Planner revises a rejected workflow before falling back to a Blueprint.
            </p>
          </label>

          <label>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 6 }}>LLM max tokens per call</div>
            <input
              type="number"
              min={200}
              max={8000}
              step={100}
              value={settings.llm_max_tokens}
              onChange={(e) => handleChange({ llm_max_tokens: Number(e.target.value) })}
              style={{ padding: "9px 14px", borderRadius: 10, border: "1px solid var(--card-border)", width: "100%" }}
            />
          </label>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button type="button" className="btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? "Saving…" : "Save changes"}
            </button>
            {saved && <span style={{ color: "var(--success)", fontSize: "0.85rem" }}>Saved</span>}
          </div>
        </div>
      </div>
    </>
  );
}
