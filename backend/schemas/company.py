from typing import Any

from pydantic import BaseModel, Field


class LeadOut(BaseModel):
    id: int
    email: str
    company_name: str | None
    status: str
    priority: str
    score: float
    created_at: str
    updated_at: str


class LeadListResponse(BaseModel):
    items: list[LeadOut]
    total: int
    page: int
    page_size: int


class InternalNoteOut(BaseModel):
    id: int
    note: str
    author_user_id: int | None
    created_at: str


class LeadDetail(LeadOut):
    demos: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[InternalNoteOut] = Field(default_factory=list)


class LeadUpdateRequest(BaseModel):
    status: str | None = None
    priority: str | None = None


class NoteCreateRequest(BaseModel):
    note: str = Field(min_length=1, max_length=4000)


class DashboardKpis(BaseModel):
    total_leads: int
    new_leads: int
    total_demos: int
    active_demos: int
    successful_demos: int
    demo_success_rate: float
    average_generation_time_ms: float
    average_critic_score: float
    qualified_lead_rate: float
    recent_leads: list[LeadOut]
    recent_demos: list[dict[str, Any]]


class AgentMetrics(BaseModel):
    agent_name: str
    status: str
    total_executions: int
    success_count: int
    failure_count: int
    success_rate: float
    average_duration_ms: float
    recent_executions: list[dict[str, Any]] = Field(default_factory=list)


class CriticMetrics(BaseModel):
    average_score: float
    approval_rate: float
    retry_rate: float
    rejected_workflow_count: int
    score_distribution: dict[str, int]


class AgentsOverview(BaseModel):
    agents: list[AgentMetrics]
    critic: CriticMetrics


class FunnelStage(BaseModel):
    stage: str
    count: int


class TrendPoint(BaseModel):
    date: str
    leads: int
    demos: int


class AnalyticsSummary(BaseModel):
    funnel: list[FunnelStage]
    trend: list[TrendPoint]
    workflow_success_rate: float
    average_requirement_fields: float


class DemoListItem(BaseModel):
    session_id: str
    title: str | None
    lead_email: str | None
    outcome: str
    critic_score: float | None
    created_at: str
    updated_at: str


class DemoListResponse(BaseModel):
    items: list[DemoListItem]
    total: int
    page: int
    page_size: int


class CompanySettingsOut(BaseModel):
    critic_approval_threshold: float
    max_planner_retries: int
    llm_max_tokens: int


class CompanySettingsUpdate(BaseModel):
    critic_approval_threshold: float | None = Field(default=None, ge=0, le=10)
    max_planner_retries: int | None = Field(default=None, ge=0, le=5)
    llm_max_tokens: int | None = Field(default=None, ge=200, le=8000)
