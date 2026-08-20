"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import ResultScreen from "@/components/ResultScreen";
import { getCompanyDemoDetail } from "@/services/companyApi";
import type { DemoResult } from "@/types/api";

export default function CompanyDemoDetailPage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const [demo, setDemo] = useState<(DemoResult & { lead_email: string | null }) | null>(null);

  useEffect(() => {
    getCompanyDemoDetail(params.sessionId)
      .then((d) => setDemo(d as unknown as DemoResult & { lead_email: string | null }))
      .catch(() => undefined);
  }, [params.sessionId]);

  if (!demo) return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;

  return (
    <>
      <div className="panel" style={{ marginBottom: 20 }}>
        <span className="panel-title">Client</span>
        <strong>{demo.lead_email ?? "Unknown"}</strong>
      </div>
      <ResultScreen result={demo} onReset={() => router.push("/company/demos")} readOnly />
    </>
  );
}
