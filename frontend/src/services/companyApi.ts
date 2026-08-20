import type {
  AgentMetrics,
  AgentsOverview,
  AnalyticsSummary,
  CompanySettings,
  CompanyUser,
  DashboardKpis,
  DemoListResponse,
  InternalNote,
  Lead,
  LeadDetail,
  LeadListResponse,
} from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "winfomi_company_token";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getCompanyToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setCompanyToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearCompanyToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
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
    throw new ApiError(typeof detail === "string" ? detail : "Request failed", res.status);
  }
  return res.json() as Promise<T>;
}

function authHeaders(): Record<string, string> {
  const token = getCompanyToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function authedGet<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const query = params
    ? "?" +
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== "")
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join("&")
    : "";
  const res = await fetch(`${BASE_URL}${path}${query}`, { headers: authHeaders() });
  return handle<T>(res);
}

export async function login(email: string, password: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/company/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await handle<{ access_token: string }>(res);
  setCompanyToken(body.access_token);
}

export async function me(): Promise<CompanyUser> {
  return authedGet<CompanyUser>("/api/company/auth/me");
}

export async function getDashboard(): Promise<DashboardKpis> {
  return authedGet<DashboardKpis>("/api/company/dashboard");
}

export async function listLeads(params: {
  status?: string;
  search?: string;
  sort?: string;
  page?: number;
  page_size?: number;
}): Promise<LeadListResponse> {
  return authedGet<LeadListResponse>("/api/company/leads", params);
}

export async function getLead(id: number): Promise<LeadDetail> {
  return authedGet<LeadDetail>(`/api/company/leads/${id}`);
}

export async function updateLead(id: number, patch: { status?: string; priority?: string }): Promise<Lead> {
  const res = await fetch(`${BASE_URL}/api/company/leads/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(patch),
  });
  return handle<Lead>(res);
}

export async function addLeadNote(id: number, note: string): Promise<InternalNote> {
  const res = await fetch(`${BASE_URL}/api/company/leads/${id}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ note }),
  });
  return handle<InternalNote>(res);
}

export async function getAgentsOverview(): Promise<AgentsOverview> {
  return authedGet<AgentsOverview>("/api/company/agents");
}

export async function getAgentDetail(name: string): Promise<AgentMetrics> {
  return authedGet<AgentMetrics>(`/api/company/agents/${name}`);
}

export async function getAnalytics(): Promise<AnalyticsSummary> {
  return authedGet<AnalyticsSummary>("/api/company/analytics");
}

export async function listDemos(params: {
  outcome?: string;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<DemoListResponse> {
  return authedGet<DemoListResponse>("/api/company/demos", params);
}

export async function getCompanyDemoDetail(sessionId: string): Promise<Record<string, unknown>> {
  return authedGet<Record<string, unknown>>(`/api/company/demos/${sessionId}`);
}

export async function getSettings(): Promise<CompanySettings> {
  return authedGet<CompanySettings>("/api/company/settings");
}

export async function updateSettings(patch: Partial<CompanySettings>): Promise<CompanySettings> {
  const res = await fetch(`${BASE_URL}/api/company/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(patch),
  });
  return handle<CompanySettings>(res);
}
