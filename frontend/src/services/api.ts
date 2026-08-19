import type { ActionLogEntry, DemoResult, ExecutionResult } from "../types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore parse failure, use statusText
    }
    throw new ApiError(typeof detail === "string" ? detail : "Request failed");
  }
  return res.json() as Promise<T>;
}

export async function createDemo(text: string): Promise<DemoResult> {
  const res = await fetch(`${BASE_URL}/api/demo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return handle<DemoResult>(res);
}

export async function getDemo(sessionId: string): Promise<DemoResult> {
  const res = await fetch(`${BASE_URL}/api/demo/${sessionId}`);
  return handle<DemoResult>(res);
}

export async function runRecord(sessionId: string, recordId: string): Promise<ExecutionResult> {
  const res = await fetch(`${BASE_URL}/api/demo/${sessionId}/records/${encodeURIComponent(recordId)}/run`, {
    method: "POST",
  });
  return handle<ExecutionResult>(res);
}

export async function takeAction(sessionId: string, recordId: string, action: string): Promise<ActionLogEntry> {
  const res = await fetch(`${BASE_URL}/api/demo/${sessionId}/records/${encodeURIComponent(recordId)}/actions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  return handle<ActionLogEntry>(res);
}

export async function getActionsLog(sessionId: string): Promise<ActionLogEntry[]> {
  const res = await fetch(`${BASE_URL}/api/demo/${sessionId}/actions`);
  return handle<ActionLogEntry[]>(res);
}
