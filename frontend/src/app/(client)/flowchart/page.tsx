"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import FlowchartBuilder from "@/components/FlowchartBuilder";
import ProcessingScreen from "@/components/ProcessingScreen";
import { ApiError, getClientToken, streamDemoBuild } from "@/services/clientApi";
import type { BuildStage } from "@/services/clientApi";

type Stage = "canvas" | "building";

export default function FlowchartPage() {
  const router = useRouter();
  const [stage, setStage] = useState<Stage>("canvas");
  const [buildStage, setBuildStage] = useState<BuildStage | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!getClientToken()) router.replace("/start");
  }, [router]);

  const handleGenerate = useCallback(
    async (text: string) => {
      const requestId = ++requestIdRef.current;
      setErrorMessage(null);
      setStage("building");
      setBuildStage(null);

      try {
        const { session_id } = await streamDemoBuild(text, (s) => {
          if (requestIdRef.current === requestId) setBuildStage(s);
        });
        if (requestIdRef.current !== requestId) return;
        router.push(`/demo/${session_id}`);
      } catch (err) {
        if (requestIdRef.current !== requestId) return;
        const message = err instanceof ApiError ? err.message : "Could not reach the AI workflow service. Please try again.";
        setErrorMessage(message);
        setStage("canvas");
      }
    },
    [router]
  );

  return (
    <>
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
      {stage === "building" && <ProcessingScreen stage={buildStage} />}
    </>
  );
}
