"use client";

import { useCallback, useRef, useState } from "react";
import LandingScreen from "@/components/LandingScreen";
import ProcessingScreen from "@/components/ProcessingScreen";
import ResultScreen from "@/components/ResultScreen";
import TopBar from "@/components/TopBar";
import { ApiError, createDemo, createDemoFromFile } from "@/services/api";
import type { DemoResult } from "@/types/api";

type Stage = "landing" | "processing" | "result";

const MIN_PROCESSING_MS = 3600;

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default function Home() {
  const [stage, setStage] = useState<Stage>("landing");
  const [result, setResult] = useState<DemoResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastText, setLastText] = useState("");
  const requestIdRef = useRef(0);

  const runDemo = useCallback(async (text: string) => {
    const requestId = ++requestIdRef.current;
    setLastText(text);
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
      setStage("landing");
    }
  }, []);

  const runDemoFromFile = useCallback(async (file: File, instruction: string) => {
    const requestId = ++requestIdRef.current;
    setLastText(`Uploaded file: ${file.name}`);
    setErrorMessage(null);
    setStage("processing");

    try {
      const [demoResult] = await Promise.all([createDemoFromFile(file, instruction), sleep(MIN_PROCESSING_MS)]);
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
      setStage("landing");
    }
  }, []);

  const handleReset = useCallback(() => {
    setResult(null);
    setErrorMessage(null);
    setStage("landing");
  }, []);

  return (
    <>
      <TopBar />
      <div className="app-main-content">
        {stage === "landing" && (
          <LandingScreen
            onSubmit={runDemo}
            onSubmitFile={runDemoFromFile}
            errorMessage={errorMessage}
            initialText={lastText}
          />
        )}
        {stage === "processing" && <ProcessingScreen />}
        {stage === "result" && result && <ResultScreen result={result} onReset={handleReset} />}
      </div>
    </>
  );
}
