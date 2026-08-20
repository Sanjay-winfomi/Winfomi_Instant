import type { ActionLogEntry, DemoResult, DemoSummary, ExecutionResult } from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "winfomi_client_token";
const EMAIL_KEY = "winfomi_client_email";

export class ApiError extends Error {}

export function getClientToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getClientEmail(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(EMAIL_KEY);
}

function setClientSession(token: string, email: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(EMAIL_KEY, email);
}

export function clearClientSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(EMAIL_KEY);
}

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

function authHeaders(): Record<string, string> {
  const token = getClientToken();
  return token ? { "X-Client-Token": token } : {};
}

export async function startClientSession(email: string): Promise<{ client_token: string; email: string }> {
  const res = await fetch(`${BASE_URL}/api/client/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const body = await handle<{ client_token: string; email: string }>(res);
  setClientSession(body.client_token, body.email);
  return body;
}

export async function createDemo(text: string): Promise<DemoResult> {
  const res = await fetch(`${BASE_URL}/api/client/demo`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ text }),
  });
  return handle<DemoResult>(res);
}

export async function createDemoFromFile(file: File, instruction: string): Promise<DemoResult> {
  const formData = new FormData();
  formData.append("file", file);
  if (instruction.trim()) formData.append("instruction", instruction.trim());
  const res = await fetch(`${BASE_URL}/api/client/demo/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  return handle<DemoResult>(res);
}

export type BuildStage = "understanding" | "designing" | "validating" | "preparing";

/** Reads the real backend stage-transition stream (spec §14) via fetch's
 * ReadableStream - deliberately not the EventSource API, since we need to send
 * the X-Client-Token header and a POST body (the description can be long). */
export async function streamDemoBuild(
  text: string,
  onStage: (stage: BuildStage) => void
): Promise<{ session_id: string; outcome: string }> {
  const res = await fetch(`${BASE_URL}/api/client/demo/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ text }),
  });
  if (!res.ok || !res.body) {
    return handle(res);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const payload = line.replace(/^data:\s*/, "").trim();
      if (!payload) continue;
      const event = JSON.parse(payload);
      if (event.event === "stage") onStage(event.stage as BuildStage);
      if (event.event === "done") return { session_id: event.session_id, outcome: event.outcome };
    }
  }
  throw new ApiError("The build stream ended unexpectedly.");
}

export async function getDemo(sessionId: string): Promise<DemoResult> {
  const res = await fetch(`${BASE_URL}/api/client/demo/${sessionId}`);
  return handle<DemoResult>(res);
}

export async function modifyDemo(sessionId: string, text: string): Promise<DemoResult> {
  const res = await fetch(`${BASE_URL}/api/client/demo/${sessionId}/modify`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ text }),
  });
  return handle<DemoResult>(res);
}

export async function listMyDemos(): Promise<DemoSummary[]> {
  const res = await fetch(`${BASE_URL}/api/client/demos`, { headers: authHeaders() });
  return handle<DemoSummary[]>(res);
}

export async function runRecord(sessionId: string, recordId: string): Promise<ExecutionResult> {
  const res = await fetch(`${BASE_URL}/api/client/demo/${sessionId}/records/${encodeURIComponent(recordId)}/run`, {
    method: "POST",
    headers: authHeaders(),
  });
  return handle<ExecutionResult>(res);
}

export async function takeAction(sessionId: string, recordId: string, action: string): Promise<ActionLogEntry> {
  const res = await fetch(`${BASE_URL}/api/client/demo/${sessionId}/records/${encodeURIComponent(recordId)}/actions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ action }),
  });
  return handle<ActionLogEntry>(res);
}

export async function getActionsLog(sessionId: string): Promise<ActionLogEntry[]> {
  const res = await fetch(`${BASE_URL}/api/client/demo/${sessionId}/actions`);
  return handle<ActionLogEntry[]>(res);
}

export async function logEvent(
  eventType: string,
  sessionId?: string,
  metadata?: Record<string, unknown>
): Promise<void> {
  if (!getClientToken()) return;
  await fetch(`${BASE_URL}/api/client/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ event_type: eventType, session_id: sessionId, metadata: metadata ?? {} }),
  }).catch(() => undefined);
}
