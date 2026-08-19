export interface Requirement {
  goal: string;
  input: string;
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
}
