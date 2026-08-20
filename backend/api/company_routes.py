"""Company (Winfomi employee) API - dashboard, leads, agent/critic monitoring,
analytics, demos, settings. Every route requires a valid COMPANY_ADMIN JWT
(services/auth.get_current_company_user) - server-side enforced, never trusting
frontend role state. Never returns internal notes or raw prompts/reasoning to
clients (this router is never mounted under /api/client)."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from api.store import (
    add_note,
    dashboard_counts,
    get_lead,
    lead_email_for,
    list_agent_executions,
    list_all_demos,
    list_all_events,
    list_leads,
    list_notes,
    update_lead,
)
from api.store import get as get_session
from database.models import AgentExecution, ClientEvent, DemoSessionRecord, Lead
from schemas.company import (
    AgentMetrics,
    AgentsOverview,
    AnalyticsSummary,
    CompanySettingsOut,
    CompanySettingsUpdate,
    CriticMetrics,
    DashboardKpis,
    DemoListItem,
    DemoListResponse,
    FunnelStage,
    InternalNoteOut,
    LeadDetail,
    LeadListResponse,
    LeadOut,
    LeadUpdateRequest,
    NoteCreateRequest,
    TrendPoint,
)
from services.auth import CurrentCompanyUser, get_current_company_user
from services.settings_service import get_effective_settings, update_settings

router = APIRouter(prefix="/api/company", dependencies=[Depends(get_current_company_user)])

AGENT_NAMES = ["requirement", "planner", "critic", "executor"]
FUNNEL_EVENTS = [
    ("EMAIL_SUBMITTED", "Email Submitted"),
    ("DEMO_CREATED", "Demo Created"),
    ("DEMO_OPENED", "Demo Opened"),
    ("MINI_APP_INTERACTION", "Demo Interacted"),
    ("FULL_SOLUTION_REQUESTED", "Solution Requested"),
]


def _lead_out(lead: Lead) -> LeadOut:
    return LeadOut(
        id=lead.id,
        email=lead.email,
        company_name=lead.company_name,
        status=lead.status,
        priority=lead.priority,
        score=lead.score,
        created_at=lead.created_at.isoformat(),
        updated_at=lead.updated_at.isoformat(),
    )


def _demo_summary(record: DemoSessionRecord) -> dict:
    return {
        "session_id": record.session_id,
        "title": record.title,
        "outcome": record.outcome,
        "created_at": record.created_at.isoformat(),
    }


@router.get("/dashboard", response_model=DashboardKpis)
def dashboard() -> DashboardKpis:
    counts = dashboard_counts()
    executions = list_agent_executions()
    durations_by_session: dict[str, int] = defaultdict(int)
    for execution in executions:
        durations_by_session[execution.session_id] += execution.duration_ms
    avg_generation_time = (
        sum(durations_by_session.values()) / len(durations_by_session) if durations_by_session else 0.0
    )

    demos, _ = list_all_demos(page=1, page_size=500)
    critic_scores = [d.critic.get("overall_score") for d in demos if d.critic]
    avg_critic_score = sum(critic_scores) / len(critic_scores) if critic_scores else 0.0

    total_demos = counts["total_demos"]
    success_rate = round((counts["successful_demos"] / total_demos) * 100, 1) if total_demos else 0.0
    qualified_rate = (
        round((counts["qualified_leads"] / counts["total_leads"]) * 100, 1) if counts["total_leads"] else 0.0
    )

    return DashboardKpis(
        total_leads=counts["total_leads"],
        new_leads=counts["new_leads"],
        total_demos=total_demos,
        active_demos=counts["active_demos"],
        successful_demos=counts["successful_demos"],
        demo_success_rate=success_rate,
        average_generation_time_ms=round(avg_generation_time, 1),
        average_critic_score=round(avg_critic_score, 2),
        qualified_lead_rate=qualified_rate,
        recent_leads=[_lead_out(lead) for lead in counts["recent_leads"]],
        recent_demos=[_demo_summary(d) for d in counts["recent_demos"]],
    )


@router.get("/leads", response_model=LeadListResponse)
def leads(
    status: str | None = None,
    search: str | None = None,
    sort: str = "-created_at",
    page: int = 1,
    page_size: int = 20,
) -> LeadListResponse:
    rows, total = list_leads(status=status, search=search, sort=sort, page=page, page_size=page_size)
    return LeadListResponse(items=[_lead_out(l) for l in rows], total=total, page=page, page_size=page_size)


@router.get("/leads/{lead_id}", response_model=LeadDetail)
def lead_detail(lead_id: int) -> LeadDetail:
    lead = get_lead(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found.")

    from api.store import list_demos_for_lead, list_events_for_lead

    demos = list_demos_for_lead(lead_id)
    events = list_events_for_lead(lead_id)
    notes = list_notes(lead_id)

    return LeadDetail(
        **_lead_out(lead).model_dump(),
        demos=[_demo_summary(d) for d in demos],
        events=[
            {"event_type": e.event_type, "session_id": e.session_id, "created_at": e.created_at.isoformat(), "metadata": e.event_metadata}
            for e in events
        ],
        notes=[
            InternalNoteOut(id=n.id, note=n.note, author_user_id=n.author_user_id, created_at=n.created_at.isoformat())
            for n in notes
        ],
    )


@router.patch("/leads/{lead_id}", response_model=LeadOut)
def patch_lead(lead_id: int, request: LeadUpdateRequest) -> LeadOut:
    lead = update_lead(lead_id, status=request.status, priority=request.priority)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return _lead_out(lead)


@router.post("/leads/{lead_id}/notes", response_model=InternalNoteOut)
def create_note(lead_id: int, request: NoteCreateRequest, current: CurrentCompanyUser = Depends(get_current_company_user)) -> InternalNoteOut:
    if get_lead(lead_id) is None:
        raise HTTPException(status_code=404, detail="Lead not found.")
    note = add_note(lead_id, current.id, request.note)
    return InternalNoteOut(id=note.id, note=note.note, author_user_id=note.author_user_id, created_at=note.created_at.isoformat())


def _agent_metrics(agent_name: str, executions: list[AgentExecution]) -> AgentMetrics:
    rows = [e for e in executions if e.agent_name == agent_name]
    success = sum(1 for e in rows if e.status == "success")
    failure = len(rows) - success
    avg_duration = sum(e.duration_ms for e in rows) / len(rows) if rows else 0.0
    return AgentMetrics(
        agent_name=agent_name,
        status="healthy" if not rows or failure / max(len(rows), 1) < 0.2 else "degraded",
        total_executions=len(rows),
        success_count=success,
        failure_count=failure,
        success_rate=round((success / len(rows)) * 100, 1) if rows else 100.0,
        average_duration_ms=round(avg_duration, 1),
        recent_executions=[
            {
                "session_id": e.session_id,
                "status": e.status,
                "duration_ms": e.duration_ms,
                "attempt": e.attempt,
                "error_message": e.error_message,
                "created_at": e.created_at.isoformat(),
            }
            for e in rows[:20]
        ],
    )


def _critic_metrics() -> CriticMetrics:
    demos, _ = list_all_demos(page=1, page_size=1000)
    all_attempts = []
    for demo in demos:
        all_attempts.extend(demo.critic_history or [])

    scores = [a["overall_score"] for a in all_attempts if "overall_score" in a]
    approved = sum(1 for a in all_attempts if a.get("approved"))
    retries = sum(1 for demo in demos if len(demo.critic_history or []) > 1)
    rejected = sum(1 for a in all_attempts if not a.get("approved"))

    distribution: dict[str, int] = defaultdict(int)
    for score in scores:
        bucket = f"{int(score)}-{int(score) + 1}"
        distribution[bucket] += 1

    return CriticMetrics(
        average_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
        approval_rate=round((approved / len(all_attempts)) * 100, 1) if all_attempts else 0.0,
        retry_rate=round((retries / len(demos)) * 100, 1) if demos else 0.0,
        rejected_workflow_count=rejected,
        score_distribution=dict(distribution),
    )


@router.get("/agents", response_model=AgentsOverview)
def agents_overview() -> AgentsOverview:
    executions = list_agent_executions()
    return AgentsOverview(
        agents=[_agent_metrics(name, executions) for name in AGENT_NAMES],
        critic=_critic_metrics(),
    )


@router.get("/agents/{agent_name}", response_model=AgentMetrics)
def agent_detail(agent_name: str) -> AgentMetrics:
    if agent_name not in AGENT_NAMES:
        raise HTTPException(status_code=404, detail="Unknown agent.")
    executions = list_agent_executions(agent_name=agent_name)
    return _agent_metrics(agent_name, executions)


@router.get("/analytics", response_model=AnalyticsSummary)
def analytics() -> AnalyticsSummary:
    events = list_all_events()
    event_counts = Counter(e.event_type for e in events)
    funnel = [FunnelStage(stage=label, count=event_counts.get(key, 0)) for key, label in FUNNEL_EVENTS]

    by_day_leads: dict[str, set] = defaultdict(set)
    by_day_demos: dict[str, set] = defaultdict(set)
    for e in events:
        day = e.created_at.date().isoformat()
        by_day_leads[day].add(e.lead_id)
        if e.event_type == "DEMO_CREATED" and e.session_id:
            by_day_demos[day].add(e.session_id)

    days = sorted(set(by_day_leads) | set(by_day_demos))
    trend = [TrendPoint(date=d, leads=len(by_day_leads.get(d, set())), demos=len(by_day_demos.get(d, set()))) for d in days]

    demos, total_demos = list_all_demos(page=1, page_size=1000)
    successful = sum(1 for d in demos if d.outcome == "executed")
    workflow_success_rate = round((successful / total_demos) * 100, 1) if total_demos else 0.0
    field_counts = [len((d.requirement or {}).get("fields", [])) for d in demos if d.requirement]
    avg_fields = round(sum(field_counts) / len(field_counts), 2) if field_counts else 0.0

    return AnalyticsSummary(
        funnel=funnel,
        trend=trend,
        workflow_success_rate=workflow_success_rate,
        average_requirement_fields=avg_fields,
    )


@router.get("/demos", response_model=DemoListResponse)
def demos(outcome: str | None = None, search: str | None = None, page: int = 1, page_size: int = 20) -> DemoListResponse:
    rows, total = list_all_demos(outcome=outcome, search=search, page=page, page_size=page_size)
    items = [
        DemoListItem(
            session_id=r.session_id,
            title=r.title,
            lead_email=lead_email_for(r.lead_id),
            outcome=r.outcome,
            critic_score=(r.critic or {}).get("overall_score"),
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )
        for r in rows
    ]
    return DemoListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/demos/{session_id}")
def demo_detail(session_id: str) -> dict:
    result = get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")
    payload = result.model_dump()
    payload["lead_email"] = lead_email_for(result.lead_id)
    return payload


@router.get("/settings", response_model=CompanySettingsOut)
def read_settings() -> CompanySettingsOut:
    effective = get_effective_settings()
    return CompanySettingsOut(
        critic_approval_threshold=effective.critic_approval_threshold,
        max_planner_retries=effective.max_planner_retries,
        llm_max_tokens=effective.llm_max_tokens,
    )


@router.put("/settings", response_model=CompanySettingsOut)
def write_settings(request: CompanySettingsUpdate) -> CompanySettingsOut:
    values = {k: v for k, v in request.model_dump().items() if v is not None}
    effective = update_settings(values)
    return CompanySettingsOut(
        critic_approval_threshold=effective.critic_approval_threshold,
        max_planner_retries=effective.max_planner_retries,
        llm_max_tokens=effective.llm_max_tokens,
    )
