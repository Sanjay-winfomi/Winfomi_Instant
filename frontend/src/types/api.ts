export interface Requirement {
  goal: string;
  input: string;
  record_label: string;
  fields: string[];
  decision: string | null;
  condition: string | null;
  action: string;
  expected_output: string;
}

export interface WorkflowStep {
  tool: string;
  params: Record<string, unknown>;
}

export interface Workflow {
  steps: WorkflowStep[];
}

export interface CriticScores {
  requirement_understanding: number;
  workflow_completeness: number;
  logical_correctness: number;
  tool_feasibility: number;
}

export interface CriticResult {
  scores: CriticScores;
  overall_score: number;
  approved: boolean;
  feedback: string[];
  attempt: number;
}

export interface StepResult {
  tool: string;
  params: Record<string, unknown>;
  status: "success" | "failed" | "blocked";
  output: unknown;
  error?: string | null;
  duration_ms: number;
}

export interface ExecutionResult {
  status: "success" | "partial" | "blueprint";
  step_results: StepResult[];
  final_output: unknown;
}

export interface WorkflowBlueprint {
  requirement_analysis: Record<string, unknown>;
  proposed_workflow: WorkflowStep[];
  tools_required: string[];
  expected_output_description: string;
  integration_note: string;
}

export interface RejectedStep {
  tool: string | null;
  reason: string;
}

export interface RecordSummary {
  id: string;
  label: string;
}

export interface ActionOption {
  action: string;
  label: string;
}

export interface MiniAppInfo {
  dataset: string | null;
  records: RecordSummary[];
  actions: ActionOption[];
}

export interface ActionLogEntry {
  record_id: string;
  action: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Dynamic mini-app UI schema - what DynamicMiniAppRenderer consumes instead of
// one fixed hardcoded template (mirrors backend/schemas/ui_schema.py).
// ---------------------------------------------------------------------------

export interface UiInput {
  id: string;
  type: "text" | "number" | "date" | "select" | "record_picker";
  label: string;
  field: string | null;
  options: string[] | null;
}

export interface UiAction {
  id: string;
  type: "run" | "record_action";
  label: string;
  action: string | null;
}

export interface UiResult {
  id: string;
  type: "table" | "card" | "status";
  title: string;
  columns?: string[] | null;
  rows?: Record<string, unknown>[] | null;
  content?: unknown;
}

export interface UiComponent {
  ref: string;
}

export interface UiSchema {
  app: { title: string; description: string };
  inputs: UiInput[];
  actions: UiAction[];
  results: UiResult[];
  components: UiComponent[];
}

export interface DemoResult {
  session_id: string;
  outcome: "executed" | "blueprint" | "error";
  requirement: Requirement | null;
  workflow: Workflow | null;
  critic: CriticResult | null;
  critic_history: CriticResult[];
  execution: ExecutionResult | null;
  blueprint: WorkflowBlueprint | null;
  rejected_steps: RejectedStep[];
  mode: "live" | "fallback";
  error?: string | null;
  mini_app: MiniAppInfo | null;
  ui_schema: UiSchema | null;
  title: string | null;
}

export interface DemoSummary {
  session_id: string;
  title: string | null;
  outcome: string;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Company portal types
// ---------------------------------------------------------------------------

export interface CompanyUser {
  id: number;
  email: string;
  name: string;
  role: string;
}

export interface Lead {
  id: number;
  email: string;
  company_name: string | null;
  status: string;
  priority: string;
  score: number;
  created_at: string;
  updated_at: string;
}

export interface InternalNote {
  id: number;
  note: string;
  author_user_id: number | null;
  created_at: string;
}

export interface LeadDetail extends Lead {
  demos: DemoSummary[];
  events: { event_type: string; session_id: string | null; created_at: string; metadata: Record<string, unknown> }[];
  notes: InternalNote[];
}

export interface LeadListResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardKpis {
  total_leads: number;
  new_leads: number;
  total_demos: number;
  active_demos: number;
  successful_demos: number;
  demo_success_rate: number;
  average_generation_time_ms: number;
  average_critic_score: number;
  qualified_lead_rate: number;
  recent_leads: Lead[];
  recent_demos: { session_id: string; title: string | null; outcome: string; created_at: string }[];
}

export interface AgentMetrics {
  agent_name: string;
  status: string;
  total_executions: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  average_duration_ms: number;
  recent_executions: {
    session_id: string;
    status: string;
    duration_ms: number;
    attempt: number;
    error_message: string | null;
    created_at: string;
  }[];
}

export interface CriticMetrics {
  average_score: number;
  approval_rate: number;
  retry_rate: number;
  rejected_workflow_count: number;
  score_distribution: Record<string, number>;
}

export interface AgentsOverview {
  agents: AgentMetrics[];
  critic: CriticMetrics;
}

export interface AnalyticsSummary {
  funnel: { stage: string; count: number }[];
  trend: { date: string; leads: number; demos: number }[];
  workflow_success_rate: number;
  average_requirement_fields: number;
}

export interface DemoListItem {
  session_id: string;
  title: string | null;
  lead_email: string | null;
  outcome: string;
  critic_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface DemoListResponse {
  items: DemoListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CompanySettings {
  critic_approval_threshold: number;
  max_planner_retries: number;
  llm_max_tokens: number;
}
