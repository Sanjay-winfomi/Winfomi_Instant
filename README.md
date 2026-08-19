# Self-Serve Instant AI Agent Sandbox

> "Instead of booking a demo, a potential client describes their business problem in
> plain English and gets an interactive AI-agent prototype instantly."

Replaces the traditional B2B presales flow (contact → sales → requirement discussion →
presales engineer → scheduled demo) with an instant self-serve one: type a business
problem, watch four AI agents design, validate, and **actually run** a small workflow
against real mock data, and interact with the result — all in seconds.

## Features

- **Generic 4-agent pipeline** — Requirement Analyzer → Planner → Critic → Executor,
  orchestrated with LangGraph. No per-use-case hardcoding: every request, anticipated
  or not, flows through the same graph.
- **Tool Registry safety layer** — the Planner may only reference 18 fixed, deterministic
  tools (`READ_DATA`, `CLASSIFY`, `CHECK_CONDITION`, `ROUTE`, …). Any hallucinated tool
  name is rejected before it reaches the Critic; rejections are shown on the result
  screen for transparency.
- **Deterministic Critic gate** — scores every workflow 0–10 across 4 equally-weighted
  criteria. The overall score is always recomputed in Python from the sub-scores (never
  trusts the model's own claimed total). Workflows scoring below 8.0 are sent back to
  the Planner with feedback, up to 2 retries, before falling back to a Blueprint.
- **Real execution, not scripted output** — the Executor runs each approved step against
  actual mock datasets (`backend/mock_data/*.json`) and returns real per-step results.
- **"Never dead-end" fallback** — if a request needs a data field the mock dataset
  genuinely doesn't have (e.g. employee attendance tracking), the Executor detects the
  capability gap and the app renders a **Workflow Blueprint** (what was understood, the
  proposed workflow, tools required, and what integration would be needed) instead of an
  error.
- **Demo-safe by default** — with no LLM API key configured, every agent falls back to a
  deterministic, rule-based implementation, so the full pipeline — including the Critic
  retry loop and Blueprint fallback — is fully demoable with zero external dependencies.
- **Live workflow visualization** — React Flow diagram of the generated workflow, with
  per-step status/duration once executed.
- **Real persistence** — every demo session (requirement, workflow, critic scores,
  execution trace, blueprint) is written to PostgreSQL, so a session survives a backend
  restart and can be inspected directly in pgAdmin4.
- **"Try it live" mini-app** — once a workflow executes, pick any real record from the
  dataset it used (a specific ticket, customer, invoice, product, or inventory item)
  and re-run the same approved workflow against just that one record, then take a
  domain-appropriate action (approve, escalate, alert supplier, …) — a genuine action,
  persisted to PostgreSQL, not a decorative button.

## Architecture

```
frontend/ (Next.js + React + TS, App Router)
  Landing screen → Processing animation → Result screen
      │ workflow diagram (React Flow), Critic score, execution trace / blueprint
      ▼
backend/ (FastAPI)
  POST /api/demo  ──▶  graph/orchestrator.py (LangGraph)
                          │
              ┌───────────┼────────────────────────────┐
              ▼           ▼            ▼                ▼
       Requirement    Planner   graph/validation.py   Critic
        Agent         Agent     (Tool Registry gate)   Agent
       (agents/*.py, deterministic fallback + optional live LLM via agents/llm_provider.py)
              │
              ▼ (critic.approved)
          Executor Agent ──▶ tools/registry.py ──▶ backend/mock_data/*.json
              │
              ▼ (capability gap)
        Workflow Blueprint
              │
              ▼ (every outcome)
   api/store.py ──▶ PostgreSQL (demo_sessions table)

  "Try it live" (frontend/src/components/MiniApp.tsx):
   pick record ──▶ POST /records/{id}/run ──▶ Executor (single-record re-run)
   take action ──▶ POST /records/{id}/actions ──▶ PostgreSQL (session_actions table)
```

LangGraph models the graph exactly as: `analyze_requirement → plan_workflow →
validate_workflow → critic_review → (retry to plan_workflow / execute_workflow /
build_blueprint)`. See `backend/graph/orchestrator.py`.

## Technology Stack

- **Frontend:** Next.js 16 (App Router) + React 19 + TypeScript, React Flow for the
  workflow diagram. The whole app is a single client component (`"use client"` on
  `src/app/page.tsx`) - three-stage local state (`landing | processing | result`) is
  all the flow needs; no server-side data fetching or extra state library.
- **Backend:** FastAPI + Pydantic v2 for request/response/schema validation.
- **Agent framework:** LangGraph (`StateGraph`) for the 4-agent orchestration and the
  Critic retry loop.
- **LLM:** Anthropic Claude, wired behind a small `LLMProvider` abstraction
  (`backend/agents/llm_provider.py`) so OpenAI/Gemini can be added later without
  touching any agent code — only `LLM_PROVIDER` and one new subclass.
- **Data:** flat JSON mock datasets (`backend/mock_data/`) that the Executor's tools
  actually operate on, plus **PostgreSQL** for demo-session persistence — via
  SQLAlchemy 2.0 (`backend/database/`), with tables created automatically on startup
  (`database/init_db.py`). Every DB access goes through `backend/api/store.py`; no
  other module touches SQLAlchemy directly.

## Project Structure

```
backend/
  agents/            the 4 agents + the LLM provider abstraction
  tools/             the Tool Registry (18 deterministic tools) + mock dataset loader
  graph/             LangGraph orchestration + the safety/validation layer
  schemas/           Pydantic contracts shared by every agent and the API
  database/          SQLAlchemy engine/session, ORM model, table creation
  api/               FastAPI routes + PostgreSQL-backed session store
  mock_data/         tickets, customers, employees, inventory, invoices, products
  tests/             unit + integration + end-to-end fixture tests
  main.py            FastAPI app entrypoint (creates DB tables on startup)
frontend/
  src/app/           layout.tsx (root layout + globals.css), page.tsx (the whole app,
                     a single "use client" component: landing/processing/result state)
  src/components/    LandingScreen, ProcessingScreen, ResultScreen, WorkflowDiagram,
                     CriticScoreCard, ExecutionTrace, BlueprintView, MiniApp
  src/services/api.ts  typed fetch client
  src/types/api.ts     TypeScript types mirroring the backend Pydantic schemas
.env.example         all required/optional environment variables
```

## Installation

Prerequisites: Python 3.11+, Node.js 18+, and a running PostgreSQL server (pgAdmin4 is
the recommended way to manage it — install [pgAdmin4](https://www.pgadmin.org/), which
bundles/connects to PostgreSQL, or point at any existing Postgres instance).

```bash
# 1. Create the database (once) - open pgAdmin4, connect to your Postgres server,
#    right-click "Databases" -> Create -> Database..., name it "agent_sandbox".
#    Or, in pgAdmin4's Query Tool against the "postgres" database:
#    CREATE DATABASE agent_sandbox;

# 2. Backend
cd backend
python -m venv .venv
./.venv/Scripts/activate        # Windows: .venv\Scripts\activate ; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 3. Frontend
cd ../frontend
npm install
```

Tables (`demo_sessions`) are created automatically the first time the backend starts —
refresh pgAdmin4's Schemas > public > Tables view afterwards to see them.

## Environment Variables

Copy `.env.example` to `.env` in the project root (values are read via
`pydantic-settings`; the backend also works with **zero** configuration — it will run
entirely in deterministic fallback mode).

| Variable | Required | Purpose |
|---|---|---|
| `LLM_PROVIDER` | No (default `anthropic`) | `anthropic` \| `openai` \| `gemini` (only `anthropic` is implemented; others fall back automatically) |
| `ANTHROPIC_API_KEY` | No | Enables live LLM calls for all 3 LLM-backed agents. Get one at console.anthropic.com |
| `LLM_MODEL` | No | Defaults to `claude-sonnet-5` |
| `LLM_MAX_TOKENS` | No | Defaults to `1500` |
| `CRITIC_APPROVAL_THRESHOLD` | No | Defaults to `8.0` |
| `MAX_PLANNER_RETRIES` | No | Defaults to `2` |
| `CORS_ORIGINS` | No | Defaults to `http://localhost:3000` (Next.js's default dev port) |
| `DATABASE_URL` | No | Defaults to `postgresql+psycopg2://postgres:postgres@localhost:5432/agent_sandbox` — update the user/password/host/port to match your PostgreSQL setup |

For the frontend, copy `frontend/.env.example` to `frontend/.env.local` (Next.js's
convention for local overrides - `.env.example` itself is never read):

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Defaults to `http://localhost:8000`. Must be prefixed `NEXT_PUBLIC_` to be readable in the browser - Next.js inlines it at build time |

`SLACK_TOKEN`, `EMAIL_SERVICE_API_KEY`, `CRM_API_KEY` are listed in
`.env.example` as stretch goals only — nothing in the MVP reads them.

## Running Locally

```bash
# Terminal 1 - backend
cd backend
./.venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000

# Terminal 2 - frontend
cd frontend
npm run dev
```

Open http://localhost:3000. With no `ANTHROPIC_API_KEY` set, every demo runs in **Demo
fallback mode** (shown as a badge on the result screen) — this is expected and fully
functional, not an error state.

## Testing

```bash
cd backend
./.venv/Scripts/python.exe -m pytest -q
```

Requires PostgreSQL to be running and reachable via `DATABASE_URL` — the API tests
exercise the real `demo_sessions` table (via `TestClient` as a context manager, so the
FastAPI lifespan/`init_db()` runs first).

32 tests covering: Requirement Agent schema output, Planner tool-registry compliance,
Critic scoring determinism, workflow validation (hallucinated tools + step-count limits),
tool execution, the API endpoints (including 422 on invalid input and 404 on unknown
sessions), the mini-app endpoints (single-record run, valid/invalid action persistence,
action log), and 5 end-to-end fixtures run through the *same* generic pipeline —
including the deliberately out-of-scope "employee attendance" case, which proves the
engine generates a Blueprint for a genuinely novel domain instead of either crashing or
being a hardcoded demo.

Frontend has no separate test runner configured for the MVP; it was verified with a
Playwright-driven browser pass through the full user journey (landing → example chip →
submit → processing animation → executed result with workflow diagram/critic
score/execution trace → reset → out-of-scope input → Blueprint view) and through the
"try it live" mini-app (pick a record → run → take an action → confirm it's persisted
in PostgreSQL), confirming zero console errors both times.

## API Documentation

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness check |
| `POST` | `/api/demo` | Body: `{"text": "..."}` (5–2000 chars). Runs the full pipeline synchronously and returns a `DemoResult` (includes `mini_app` when `outcome` is `"executed"`) |
| `GET` | `/api/demo/{session_id}` | Re-fetch a previously generated result |
| `POST` | `/api/demo/{session_id}/records/{record_id}/run` | Re-runs the session's approved workflow against just this one record; returns an `ExecutionResult` |
| `POST` | `/api/demo/{session_id}/records/{record_id}/actions` | Body: `{"action": "..."}` — must be one of the actions listed in that session's `mini_app.actions`. Persists the action and returns an `ActionLogEntry` |
| `GET` | `/api/demo/{session_id}/actions` | Lists every action taken on this session, most recent first |

Interactive OpenAPI docs are available at `http://localhost:8000/docs` once the backend
is running.

## Deployment

This MVP is designed to run as two independent processes (no Docker Compose is included
— not required by the current scope):

- **Backend:** any ASGI host (Render, Fly.io, a VM) running
  `uvicorn main:app --host 0.0.0.0 --port $PORT`. Set `ANTHROPIC_API_KEY`,
  `CORS_ORIGINS` (your deployed frontend origin), and `DATABASE_URL` (pointing at a
  managed PostgreSQL instance) as environment variables.
- **Frontend:** `npm run build && npm run start` runs it as a Node server (the default -
  deploys cleanly to Vercel, or any Node host). Set `NEXT_PUBLIC_API_BASE_URL` to the
  deployed backend URL before building, since it's inlined into the client bundle at
  build time, not read at runtime.

## Troubleshooting

- **"Could not reach the AI workflow service"** on the landing page → the backend isn't
  running or `NEXT_PUBLIC_API_BASE_URL` doesn't match its address/port.
- **Every result says "Demo fallback mode"** → this is expected with no
  `ANTHROPIC_API_KEY` set. It's a fully functional deterministic mode, not a bug.
- **A request unexpectedly returns a Workflow Blueprint** → the Executor detected that a
  planned step needs a data field that doesn't exist anywhere in the target mock
  dataset. This is the intended "no dead end" behavior for genuinely unsupported
  domains, not a failure.
- **CORS errors in the browser console** → add your frontend's origin to `CORS_ORIGINS`
  in the backend's `.env`.
- **`sqlalchemy.exc.OperationalError` / "connection refused" on startup** → PostgreSQL
  isn't running, or `DATABASE_URL` doesn't match your server's host/port/credentials.
  Check the connection in pgAdmin4 first.
- **`relation "demo_sessions" does not exist`** → the backend never got as far as its
  startup step (crashed before `init_db()` ran, or a different `DATABASE_URL` was used
  between runs) — restart it and check the startup logs for a PostgreSQL error.

## Known Limitations

- Only Anthropic is implemented as a live LLM provider; OpenAI/Gemini are stubbed to
  fall back to deterministic mode until implemented.
- The Executor's capability-gap detection is field-existence based (does the target
  dataset have this column at all) — it can't detect subtler unsupported cases where a
  field exists but the *semantics* don't match what was asked.
- No authentication — acceptable for a self-serve public demo sandbox, not for handling
  sensitive customer data.
- Schema changes are applied via `Base.metadata.create_all()` (new tables only, no
  migration history) — fine for this MVP's tables; a schema that evolves further should
  move to Alembic.
- Mini-app actions (approve, escalate, alert supplier, …) are simulated and persisted
  to PostgreSQL for audit purposes, but don't trigger any real external system (no
  actual email/Slack/CRM call) — consistent with the Tool Registry's "no arbitrary
  outbound calls" safety rule for this MVP.

## Recommended Next Improvements

- Stream intermediate agent/step events over Server-Sent Events instead of the
  client-side fixed-duration animation, once the Executor does real (slower) I/O.
- Add Alembic migrations once the schema needs to evolve beyond `create_all()`.
- Add a lead-capture step ("Request Full Solution") wired to a CRM, once product
  scope calls for it.
- Add OpenAI/Gemini `LLMProvider` implementations behind the existing abstraction.
