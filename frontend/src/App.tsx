import { useCallback, useRef, useState } from "react";
import "./App.css";
import LandingScreen from "./components/LandingScreen";
import ProcessingScreen from "./components/ProcessingScreen";
import ResultScreen from "./components/ResultScreen";
import { ApiError, createDemo } from "./services/api";
import type { DemoResult } from "./types/api";

type Stage = "landing" | "processing" | "result";

const MIN_PROCESSING_MS = 3600;

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function App() {
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

  const handleReset = useCallback(() => {
    setResult(null);
    setErrorMessage(null);
    setStage("landing");
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">◈</span>
          <span>Instant AI Agent Sandbox</span>
        </div>
        <div className="brand-tagline">Describe it. Watch it build itself. Try it live.</div>
      </header>

      <main className="app-main">
        {stage === "landing" && (
          <LandingScreen onSubmit={runDemo} errorMessage={errorMessage} initialText={lastText} />
        )}
        {stage === "processing" && <ProcessingScreen />}
        {stage === "result" && result && <ResultScreen result={result} onReset={handleReset} />}
      </main>
    </div>
  );
}

export default App;
