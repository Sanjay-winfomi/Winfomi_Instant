"use client";

import Link from "next/link";
import { useState } from "react";
import HeroIllustration from "@/components/HeroIllustration";
import { getClientToken } from "@/services/clientApi";
import "@/components/LandingScreen.css";

const STEPS = [
  { title: "Describe", desc: "Tell us your business problem in plain English — no forms, no categories to pick." },
  { title: "AI Understands", desc: "The Requirement Agent structures your goal, inputs, and the decision behind it." },
  { title: "AI Builds", desc: "A Planner composes a workflow from a controlled set of safe, deterministic tools." },
  { title: "AI Validates", desc: "A Critic scores the workflow and sends it back for revision until it's solid." },
  { title: "Experience", desc: "A real, interactive mini web app is generated — not a mockup — for you to try." },
];

export default function MarketingLandingPage() {
  const [hasSession] = useState(() => Boolean(getClientToken()));

  const primaryHref = hasSession ? "/create" : "/start";

  return (
    <section className="landing">
      <div className="landing-hero">
        <div className="landing-copy">
          <h1>
            Describe your problem. <span className="gradient-text">Experience the solution instantly.</span>
          </h1>
          <p>
            Winfomi Instant AI turns any reasonable business requirement into a working, interactive prototype in
            minutes — understood, designed, validated, and run by AI agents, not a template picked from a list.
          </p>
          <div style={{ display: "flex", gap: 14, marginTop: 24, flexWrap: "wrap" }}>
            <Link href={primaryHref} className="btn-primary">
              Build My AI Demo
            </Link>
          </div>
        </div>
        <HeroIllustration />
      </div>

      <div className="trust-bar" style={{ gridTemplateColumns: "repeat(5, 1fr)" }}>
        {STEPS.map((s, i) => (
          <div className="trust-item" key={s.title}>
            <span className="trust-icon">{i + 1}</span>
            <span className="trust-label">{s.title}</span>
            <span className="trust-desc">{s.desc}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
