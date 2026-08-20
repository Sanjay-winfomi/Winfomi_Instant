# Winfomi Instant AI

> **Client:** "Describe your problem → Experience your solution."
> **Company:** "Monitor leads → Monitor agents → Analyze performance → Inspect demos."

A single platform, two portals, one shared backend/AI engine/database. A prospect
describes a business problem in plain English; a 4-agent AI pipeline understands it,
designs a workflow from a fixed safe tool registry, validates it, executes it against
a tailored sample dataset, and renders a real interactive mini web app — not a
mockup. Winfomi employees monitor the resulting leads, agent/critic health,
analytics, and generated demos from a separate, authenticated company portal.

The platform is deliberately **generic**: there is no fixed list of business
categories, no pre-built demo applications, and no per-domain hardcoded logic
anywhere in the pipeline. A business problem nobody anticipated is handled by the
same code path as a familiar one.

## Two portals, one backend

```
                    WINFOMI PLATFORM
                           │
             ┌─────────────┴─────────────┐
        CLIENT PORTAL               COMPANY PORTAL
      (no auth - email only)      (JWT + bcrypt, COMPANY_ADMIN)
        Landing                       Dashboard
        Start (email capture)         Leads (scoring, notes, status)
        Create Demo                   Agents (+ Critic monitoring)
        My Demo / Demos               Analytics (funnel + trends)
        Modify / Request solution     Demos (incl. mini-app preview)
        Flowchart builder             Settings (critic threshold, retries, tokens)
             │                           │
             └──────────┬────────────────┘
                        │
                 SHARED BACKEND (FastAPI)
                        │
        ┌───────────────┼────────────────┐
     AI AGENTS      PostgreSQL      Dynamic Mini-App Engine
   (LangGraph)     (SQLAlchemy)     (tools/ui_schema.py)
```

## The AI pipeline

```
customer text ──▶ Requirement Agent ──▶ Planner Agent ──▶ Tool Registry validation
                                                                    │
                                                                    ▼
                          Executor Agent  ◀── (approved)  ◀──  Critic Agent
                                │                                  ▲
                                ▼                          (rejected, retries left)
                        UI Schema (tools/ui_schema.py)             │
                                │                          back to Planner Agent
                                ▼                                  │
                     Dynamic Mini-App (frontend)          (retries exhausted)
                                                                    ▼
                                                            Workflow Blueprint
```

- **Requirement Agent** — natural language → structured `{goal, input, record_label,
  fields, decision, condition, action, expected_output}`. Never maps onto a fixed set
  of business categories.
- **Planner Agent** — composes a 3–7 step workflow using ONLY the 18 deterministic
  tools in `tools/registry.py` (`READ_DATA`, `CLASSIFY`, `CHECK_CONDITION`, `ROUTE`, …).
- **Tool Registry validation** (`graph/validation.py`) — strips any hallucinated tool
  name before the Critic ever sees it; the model can never trigger arbitrary code.
- **Critic Agent** — scores 4 sub-criteria 0–10; `overall_score` is always recomputed
  deterministically in Python (never trusts the model's own claimed total). Below the
  threshold (default 8.0, company-configurable) sends feedback back to the Planner, up
  to a configurable retry count, before falling back to a Workflow Blueprint.
- **Executor Agent** — deterministic, never calls an LLM, only ever processes the
  sample dataset it's handed (synthesized fresh per requirement, or a customer's own
  uploaded CSV/Excel rows).
- **Dynamic Mini-App Engine** (`tools/ui_schema.py`) — deterministically derives a UI
  schema (`inputs`/`actions`/`results`/`components`) from the Requirement + Workflow +
  ExecutionResult already computed above — no LLM, no per-domain hardcoding. The
  frontend's `DynamicMiniAppRenderer` renders it through a fixed set of safe,
  extensible components (table, card, status, record picker, run/action buttons).

Every node run is instrumented (`AgentExecution` rows) for the company Agents page;
never exposes prompts or model reasoning, only safe operational metadata (status,
duration, attempt, error category).

## Client experience

`/` (marketing) → `/start` (email capture, creates a `Lead` + opaque `client_token`) →
`/create` (describe the problem) → real-time build progress driven by actual backend
stage events over a streamed response (`POST /api/client/demo/stream`, spec §14 — never
a fake timer) → `/demo/{session_id}` ("My Demo": the generated workflow diagram, critic
score, execution trace, and the interactive `DynamicMiniAppRenderer`) → optionally
"Modify this solution" (natural-language refinement, re-enters the same pipeline
against the same session) → "Request Full Solution" (lead-qualifying CTA). `/demos`
lists a client's past demos. `/flowchart` is a bonus manual workflow-diagram builder
that feeds the same pipeline.

Client identity is intentionally lightweight: an email plus an opaque `client_token`
(stored in `localStorage`, sent as `X-Client-Token`) tied to a `Lead` row — no
password, no session expiry, matching a public self-serve demo experience.

## Company portal

JWT + bcrypt auth (`/api/company/auth/login`), enforced **server-side** on every
`/api/company/*` route (`services/auth.get_current_company_user` — a FastAPI
dependency, never a frontend-only check). Sidebar: Dashboard, Leads, Agents,
Analytics, Demos, and Settings — no "Create Demo", no pricing/upgrade UI, no
notification bell (explicitly out of scope per the product spec).

- **Dashboard** — real KPIs (leads, demos, success rate, avg. critic score, avg.
  generation time, qualified-lead rate) computed from stored data, never hardcoded.
- **Leads** — searchable/filterable/sortable/paginated list; detail view shows
  activity, demos, critic score, and **internal notes** (never exposed to any
  `/api/client/*` route). Status (`NEW → ENGAGED → QUALIFIED → CONTACTED → CONVERTED
  → CLOSED`) and priority are editable.
- **Lead scoring** (`services/lead_scoring.py`) — a deterministic, configurable
  weighted sum over logged `client_events` (email submitted, demo created/opened,
  interaction, modified, full solution requested). No LLM involved.
- **Agents** — per-agent (requirement/planner/critic/executor) execution counts,
  success rate, avg. duration, recent runs; a dedicated critic-quality panel (average
  score, approval rate, retry rate, score distribution).
- **Analytics** — a lead funnel (email submitted → demo created → opened →
  interacted → solution requested) and a leads/demos trend chart (Recharts), plus
  workflow success rate — all derived from real `client_events` rows.
- **Demos** — every generated session, filterable by outcome; detail view reuses the
  **exact same** `DynamicMiniAppRenderer` the client saw (read-only preview — no
  client session to attribute interactions to).
- **Settings** — critic approval threshold, max planner retries, and LLM max tokens
  are DB-backed overrides (`services/settings_service.py`) layered on top of env
  defaults; changing them takes effect on the next pipeline run. API keys and
  provider/model selection remain env-only and are never displayed or DB-writable.

## Project structure

```
backend/
  agents/            Requirement/Planner/Critic/Executor agents + data synthesizer
  tools/             Tool Registry (18 deterministic tools), mini-app + UI-schema builders
  services/          file_import, auth (JWT/bcrypt), lead_scoring, settings_service, bootstrap
  graph/             LangGraph orchestration (+ per-node instrumentation) and validation
  schemas/           Pydantic contracts: requirement/workflow/critic/execution/ui_schema/
                     client_session/auth/company
  database/          SQLAlchemy models (demo_sessions, users, leads, client_events,
                     internal_notes, agent_executions, company_settings) + engine/init
  api/
    client_routes.py   /api/client/* — session, demo (+upload/+stream/+modify), demos,
                       records/actions, events. No auth beyond an opaque client_token.
    company_routes.py  /api/company/* — dashboard, leads, agents, analytics, demos,
                       settings. Every route requires a valid COMPANY_ADMIN JWT.
    company_auth.py    /api/company/auth/login, /me
    store.py           the only module that talks to SQLAlchemy directly
  tests/             86 tests: pipeline/tool/critic unit tests, API integration tests,
                     auth/leads/events/dashboard/agents/analytics/settings/modify tests,
                     and a UI-schema generalization test across unrelated novel domains
  main.py            FastAPI entrypoint (mounts both routers, seeds one admin account)
frontend/
  src/app/(client)/    /, /start, /create, /build (inline), /demo/[sessionId], /demos,
                       /flowchart, /help — ClientSidebar layout
  src/app/company/     /login, /dashboard, /leads(+[id]), /agents(+[name]), /analytics,
                       /demos(+[sessionId]), /settings — CompanySidebar layout, JWT-guarded
  src/components/      DynamicMiniAppRenderer (the generic mini-app renderer),
                       WorkflowDiagram, CriticScoreCard, ExecutionTrace, BlueprintView,
                       LandingScreen, ProcessingScreen (real stage-driven), FlowchartBuilder
  src/services/        clientApi.ts, companyApi.ts — typed fetch clients
  src/types/api.ts      TypeScript types mirroring the backend Pydantic schemas
```

## Installation

Prerequisites: Python 3.11+, Node.js 18+, a running PostgreSQL server.

```bash
# 1. Create the database once (pgAdmin4, or): CREATE DATABASE agent_sandbox;

# 2. Backend
cd backend
python -m venv .venv
./.venv/Scripts/activate        # Windows: .venv\Scripts\activate ; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 3. Frontend
cd ../frontend
npm install
```

Tables are created automatically on first backend startup, and one COMPANY_ADMIN
account is seeded from `SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD` (defaults:
`admin@winfomi.com` / `ChangeMe123!` — **change these in production**).

## Environment variables

Copy `.env.example` to `.env` in `backend/` (also readable from the repo root).

| Variable | Required | Purpose |
|---|---|---|
| `LLM_PROVIDER` | No (default `anthropic`) | Only `anthropic` is implemented; others fall back automatically |
| `ANTHROPIC_API_KEY` | No | Enables live LLM calls; empty = deterministic fallback mode everywhere |
| `LLM_MODEL` | No | Defaults to `claude-sonnet-5` |
| `LLM_MAX_TOKENS` | No | Env default for the "LLM max tokens" company setting (default `1500`) |
| `CRITIC_APPROVAL_THRESHOLD` | No | Env default for the critic threshold company setting (default `8.0`) |
| `MAX_PLANNER_RETRIES` | No | Env default for the max-retries company setting (default `2`) |
| `CORS_ORIGINS` | No | Defaults to `http://localhost:3000` |
| `DATABASE_URL` | No | Postgres connection string |
| `JWT_SECRET` | **Yes in production** | Signs company-portal JWTs — set a real secret outside local dev |
| `JWT_EXPIRE_MINUTES` | No | Defaults to 1440 (24h) |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | No | First COMPANY_ADMIN account, seeded only if `users` is empty |

Frontend: copy `frontend/.env.example` to `frontend/.env.local`.

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Defaults to `http://localhost:8000` |

## Running locally

```bash
# Terminal 1 - backend
cd backend
./.venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000

# Terminal 2 - frontend
cd frontend
npm run dev
```

Open http://localhost:3000 for the client experience, and
http://localhost:3000/company/login for the company portal (seeded credentials
above). With no `ANTHROPIC_API_KEY` set, every demo runs in deterministic fallback
mode — fully functional, shown as a "Demo fallback mode" badge, not an error.

## Testing

```bash
cd backend
./.venv/Scripts/python.exe -m pytest -q
```

Requires PostgreSQL reachable via `DATABASE_URL`. **86 tests**, including: the
original 4-agent pipeline/tool/critic/file-import suite; company auth (login,
JWT validation, 401 on missing/invalid token, role enforcement); lead creation,
deterministic scoring, status/notes management; the generic client-event sink;
dashboard/agents/analytics endpoints reflecting real stored data; the modify-demo
flow (same session id, requirement carried forward); company settings (DB override
actually changes a subsequent pipeline run's outcome); and a **UI-schema
generalization test** that runs two unrelated, previously-unseen business domains
through `tools/ui_schema.py` and asserts the resulting schemas differ and every
component reference resolves — proof the dynamic mini-app engine isn't secretly one
hardcoded template.

Frontend: `npm run build` and `npm run lint` are clean. There is no frontend test
runner configured; this pass was verified via `next build`/`next lint` plus an
HTTP-level smoke test of every route and the full client+company API surface
(session → demo → stream → modify → demos list; login → dashboard → leads → agents
→ analytics → demos → settings) — **not** a real-browser/visual pass, since no
browser-automation tool was available in this environment. Manually clicking
through both portals in an actual browser before shipping is still recommended.

## Security notes

- All `/api/company/*` routes require a valid COMPANY_ADMIN JWT, checked server-side
  via a FastAPI dependency — the frontend's own role state is never trusted.
- Internal lead notes are stored on their own table and never serialized by any
  `/api/client/*` response.
- The Planner may only reference tools in the fixed registry; anything else is
  stripped before the Critic ever scores it. The Executor never evaluates
  LLM-generated code.
- Passwords are bcrypt-hashed (`passlib`); JWTs are HS256-signed from `JWT_SECRET`.
  **Set a strong, unique `JWT_SECRET` outside local development.**
- API keys, DB credentials, and the JWT secret are env-only — never DB-writable,
  never returned by any API response (the Settings API only exposes 3 non-secret
  tuning values).

## Known limitations

- Only Anthropic is implemented as a live LLM provider; OpenAI/Gemini fall back to
  deterministic mode until implemented.
- Deterministic fallback mode (no API key) uses keyword-cue heuristics — works for
  any input, at lower fidelity than the live LLM.
- Schema changes are applied via `Base.metadata.create_all()` (new tables only, no
  migration history) — a schema that evolves further should move to Alembic.
- Mini-app actions (approve/flag) and action tools (email/notification/ticket) are
  simulated and persisted for audit purposes, but don't call a real external system.
- The client `client_token` never expires and has no logout — acceptable for a
  public self-serve demo experience, not for sensitive customer data.
- No frontend automated test suite; verified via build/lint + HTTP-level smoke
  testing only in this pass (see Testing above).

## Recommended next steps

- Add a real browser-automation (Playwright) pass over both portals before shipping.
- Add OpenAI/Gemini `LLMProvider` implementations behind the existing abstraction.
- Move schema management to Alembic once tables need to evolve further.
- Add rate limiting / stronger anti-abuse controls on the public `/api/client/*`
  surface (currently open to anyone who can submit an email).
- Wire "Request Full Solution" to a real CRM/notification integration.
