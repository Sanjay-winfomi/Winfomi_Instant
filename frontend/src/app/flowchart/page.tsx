"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import FlowchartBuilder from "@/components/FlowchartBuilder";
import ProcessingScreen from "@/components/ProcessingScreen";
import ResultScreen from "@/components/ResultScreen";
import { ApiError, createDemo } from "@/services/api";
import type { DemoResult } from "@/types/api";

type Stage = "canvas" | "processing" | "result";

const MIN_PROCESSING_MS = 3600;

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default function FlowchartPage() {
  const [stage, setStage] = useState<Stage>("canvas");
  const [result, setResult] = useState<DemoResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  const handleGenerate = useCallback(async (text: string) => {
    const requestId = ++requestIdRef.current;
    setErrorMessage(null);
    setStage("processing");

    try {
      const [demoResult] = await Promise.all([createDemo(text), sleep(MIN_PROCESSING_MS)]);
      if (requestIdRef.current !== requestId) return;
      setResult(demoResult);
      setStage("result");
    } catch (err) {
      if (requestIdRef.current !== requestId) return;
      const message =
        err instanceof ApiError
          ? err.message
          : "Could not reach the AI workflow service. Please check that the backend is running and try again.";
      setErrorMessage(message);
      setStage("canvas");
    }
  }, []);

  const handleReset = useCallback(() => {
    setResult(null);
    setErrorMessage(null);
    setStage("canvas");
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">◈</span>
          <span>Instant AI Agent Sandbox</span>
        </div>
        <Link href="/" className="brand-tagline flowchart-back-link">
          ← Back to describing it in text
        </Link>
      </header>

      <main className="app-main">
        {stage === "canvas" && (
          <>
            <h2 className="flowchart-title">Design your workflow manually</h2>
            <p className="flowchart-subtitle">
              Drag shapes onto the canvas, connect them, and describe each step. When you&apos;re done, the same AI
              pipeline (Requirement → Planner → Critic → Executor) builds a working demo from your flowchart.
            </p>
            {errorMessage && <p className="flowchart-error">{errorMessage}</p>}
            <FlowchartBuilder onGenerate={handleGenerate} />
          </>
        )}
        {stage === "processing" && <ProcessingScreen />}
        {stage === "result" && result && <ResultScreen result={result} onReset={handleReset} />}
      </main>
    </div>
  );
}
