"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import LandingScreen from "@/components/LandingScreen";
import ProcessingScreen from "@/components/ProcessingScreen";
import { ApiError, createDemoFromFile, getClientToken, streamDemoBuild } from "@/services/clientApi";
import type { BuildStage } from "@/services/clientApi";

type Stage = "input" | "building";

export default function CreateDemoPage() {
  const router = useRouter();
  const [stage, setStage] = useState<Stage>("input");
  const [buildStage, setBuildStage] = useState<BuildStage | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastText, setLastText] = useState("");
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!getClientToken()) router.replace("/start");
  }, [router]);

  const runDemo = useCallback(
    async (text: string) => {
      const requestId = ++requestIdRef.current;
      setLastText(text);
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
        setStage("input");
      }
    },
    [router]
  );

  const runDemoFromFile = useCallback(
    async (file: File, instruction: string) => {
      const requestId = ++requestIdRef.current;
      setLastText(`Uploaded file: ${file.name}`);
      setErrorMessage(null);
      setStage("building");
      setBuildStage("understanding");

      try {
        const result = await createDemoFromFile(file, instruction);
        if (requestIdRef.current !== requestId) return;
        router.push(`/demo/${result.session_id}`);
      } catch (err) {
        if (requestIdRef.current !== requestId) return;
        const message = err instanceof ApiError ? err.message : "Could not reach the AI workflow service. Please try again.";
        setErrorMessage(message);
        setStage("input");
      }
    },
    [router]
  );

  return (
    <>
      {stage === "input" && (
        <LandingScreen onSubmit={runDemo} onSubmitFile={runDemoFromFile} errorMessage={errorMessage} initialText={lastText} />
      )}
      {stage === "building" && <ProcessingScreen stage={buildStage} />}
    </>
  );
}
