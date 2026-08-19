# Self-Serve Instant AI Agent Sandbox

> "Instead of booking a demo, a potential client describes their business problem in
> plain English and gets an interactive AI-agent prototype instantly."

Replaces the traditional B2B presales flow (contact → sales → requirement discussion →
presales engineer → scheduled demo) with an instant self-serve one: type a business
problem, watch four AI agents design, validate, and **actually run** a small workflow
against a sample dataset generated for that exact problem, and interact with the
result — all in seconds. There is no fixed set of pre-built business domains: the
sample data is synthesized fresh per request, so a problem nobody anticipated gets a
real workflow and real sample records too, not a forced fit into the wrong category.

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
- **No fixed mock datasets** — there's no hardcoded set of business domains (no
  `tickets.json`/`customers.json`/etc). Every request gets its own sample dataset,
  synthesized from the Requirement Agent's own `record_label`/`fields`
  (`backend/agents/data_synthesizer.py`): the LLM generates realistic records when
  live, a deterministic field-name-driven generator when not. The Executor then runs
  each approved step against those real (synthesized) records and returns real
  per-step results — it never calls an LLM or invents data itself.
- **"Never dead-end" fallback** — if a step ends up referencing a field that was never
  part of the synthesized data (most often a live-LLM planning mistake), the Executor
  detects the capability gap and the app renders a **Workflow Blueprint** (what was
  understood, the proposed workflow, tools required, and what integration would be
  needed) instead of an error.
- **Demo-safe by default** — with no LLM API key configured, every agent falls back to a
  deterministic, rule-based implementation, so the full pipeline — including the Critic
  retry loop and Blueprint fallback — is fully demoable with zero external dependencies.
- **Live workflow visualization** — React Flow diagram of the generated workflow, with
  per-step status/duration once executed.
- **Real persistence** — every demo session (requirement, workflow, critic scores,
  execution trace, blueprint) is written to PostgreSQL, so a session survives a backend
  restart and can be inspected directly in pgAdmin4.
- **"Try it live" mini-app** — once a workflow executes, pick any one of the
  synthesized sample records and re-run the same approved workflow against just that
  record, then take a generic decision action (Approve / Flag for review) — a genuine
  action, persisted to PostgreSQL, not a decorative button.
- **Import a document instead of typing** — upload a `.csv`/`.xlsx` and its actual rows
  become the real dataset the workflow runs against (no synthesis at all); upload a
  `.docx`/`.pdf`/`.pptx` and its extracted text is treated exactly like a typed problem
  description. See `backend/services/file_import.py`.
- **Manual flowchart builder** (`/flowchart`) — drag shapes (Start/End, Process,
  Decision) onto a canvas, connect them, and write your own step descriptions. This is
  a free-form diagram, not tied to the Tool Registry - "building the mini web app from
  it" means serializing your diagram into a plain-English description and running it
  through the *exact same* 4-agent pipeline as typed text, so no separate execution
  path exists to keep in sync.

## Architecture

```
frontend/ (Next.js + React + TS, App Router)
  Landing screen ──▶ typed text ─────────────────┐
                  ──▶ file upload (FileUploadCard)│
  /flowchart ──▶ drag-and-drop canvas ──▶ serialized text ┘
      ▼
  Processing animation → Result screen
      │ workflow diagram (React Flow), Critic score, execution trace / blueprint
      ▼
backend/ (FastAPI)
  POST /api/demo (typed text or serialized flowchart text)
  POST /api/demo/upload (file) ──▶ services/file_import.py
                          │              │
                          │    tabular (csv/xlsx): real rows bypass synthesis entirely
                          │    text (docx/pdf/pptx): extracted text used like typed text
                          ▼
                  graph/orchestrator.py (LangGraph)
                          │
              ┌───────────┼────────────────────────────┐
              ▼           ▼            ▼                ▼
       Requirement    Planner   graph/validation.py   Critic
        Agent         Agent     (Tool Registry gate)   Agent
       (agents/*.py, deterministic fallback + optional live LLM via agents/llm_provider.py)
              │
              ▼ (critic.approved)
     agents/data_synthesizer.py ──▶ sample records tailored to the requirement
       (no fixed mock datasets - LLM-generated live, deterministic fallback otherwise)
              │
              ▼
          Executor Agent ──▶ tools/registry.py (processes the synthesized records)
              │
              ▼ (capability gap: a field genuinely missing from the records)
        Workflow Blueprint
              │
              ▼ (every outcome)
   api/store.py ──▶ PostgreSQL (demo_sessions table, incl. the synthesized records)

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
- **Data:** no fixed datasets - a small sample dataset is synthesized per request
  (`backend/agents/data_synthesizer.py`) and is what the Executor's tools actually
  operate on, *unless* the customer uploaded a `.csv`/`.xlsx` file, in which case its
  real rows are used directly. **PostgreSQL** handles demo-session persistence
  (including the dataset itself, synthesized or uploaded) via SQLAlchemy 2.0
  (`backend/database/`), with tables created automatically on startup
  (`database/init_db.py`). Every DB access goes through `backend/api/store.py`; no
  other module touches SQLAlchemy directly.
- **File parsing:** `python-docx`, `pypdf`, `openpyxl`, `python-pptx` for
  `.docx`/`.pdf`/`.xlsx`/`.pptx` respectively; `.csv` uses the standard library's
  `csv` module. All isolated behind `backend/services/file_import.py`.

## Project Structure

```
backend/
  agents/            the 4 agents + the data synthesizer + the LLM provider abstraction
  tools/             the Tool Registry (18 deterministic tools) + mini-app helpers
  services/          file_import.py - docx/pdf/xlsx/csv/pptx extraction
  graph/             LangGraph orchestration + the safety/validation layer
  schemas/           Pydantic contracts shared by every agent and the API
  database/          SQLAlchemy engine/session, ORM model, table creation
  api/               FastAPI routes + PostgreSQL-backed session store
  tests/             unit + integration + end-to-end fixture tests
  main.py            FastAPI app entrypoint (creates DB tables on startup)
frontend/
  src/app/           layout.tsx (root layout + globals.css), page.tsx (the whole app,
                     a single "use client" component: landing/processing/result state)
  src/app/flowchart/ page.tsx - the manual flowchart builder route
  src/components/    LandingScreen, ProcessingScreen, ResultScreen, WorkflowDiagram,
                     CriticScoreCard, ExecutionTrace, BlueprintView, MiniApp,
                     FileUploadCard, FlowchartBuilder
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

47 tests covering: Requirement Agent schema output (including on a genuinely novel
domain with no analogue in any hand-built dataset), Planner tool-registry compliance,
the data synthesizer (generates every requested field plus a stable `id`), Critic
scoring determinism, workflow validation (hallucinated tools + step-count limits),
tool execution (`READ_DATA` reading from injected synthesized records, not a file;
`ROUTE` tagging with a Planner-supplied team name, not a fixed employee directory),
the API endpoints (including 422 on invalid input and 404 on unknown sessions), the
mini-app endpoints (single-record run, valid/invalid action persistence, action log),
file extraction for every supported format (csv/xlsx are tabular with real rows;
docx/pdf/pptx are text, including a regression test for CSV numeric-string coercion
that a live browser test caught - `risk_score="72"` silently failed every numeric
comparison until fixed), and 5 end-to-end fixtures run through the *same* generic
pipeline for genuinely different domains — including one that exists nowhere in any
pre-built dataset, and a capability-gap test proving the Blueprint fallback still
fires correctly when a step references a field that was never synthesized.

Frontend has no separate test runner configured for the MVP; it was verified with
Playwright-driven browser passes through: the full typed-text journey (landing →
example chip → submit → processing animation → executed result with workflow
diagram/critic score/execution trace → reset → out-of-scope input → Blueprint view),
the "try it live" mini-app (pick a record → run → take an action → confirm it's
persisted in PostgreSQL), a CSV file upload (confirms the real uploaded values appear
in the result, not synthesized ones), and the flowchart builder (drag two shapes onto
the canvas via real mouse drag events, fill their text, generate a demo from them) —
confirming zero console errors across all of them.

## API Documentation

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness check |
| `POST` | `/api/demo` | Body: `{"text": "..."}` (5–2000 chars). Runs the full pipeline synchronously and returns a `DemoResult` (includes `mini_app` when `outcome` is `"executed"`) |
| `POST` | `/api/demo/upload` | Multipart form: `file` (`.csv`/`.xlsx`/`.docx`/`.pdf`/`.pptx`, max 5 MB) + optional `instruction` text. Same `DemoResult` response as `/api/demo` |
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
  planned step needs a field that was never part of the synthesized sample data
  (usually a live-LLM planning step referencing a field it invented rather than one
  from the Requirement's own `fields`). This is the intended "no dead end" behavior,
  not a failure.
- **CORS errors in the browser console** → add your frontend's origin to `CORS_ORIGINS`
  in the backend's `.env`.
- **`sqlalchemy.exc.OperationalError` / "connection refused" on startup** → PostgreSQL
  isn't running, or `DATABASE_URL` doesn't match your server's host/port/credentials.
  Check the connection in pgAdmin4 first.
- **`relation "demo_sessions" does not exist`** → the backend never got as far as its
  startup step (crashed before `init_db()` ran, or a different `DATABASE_URL` was used
  between runs) — restart it and check the startup logs for a PostgreSQL error.
- **File upload returns 415** → the extension isn't one of `.csv`/`.xlsx`/`.xls`/`.docx`/`.pdf`/`.pptx`.
- **File upload returns 422 "no readable text/rows"** → the file parsed but had no
  header row (csv/xlsx), no first-sheet data, or no extractable text (a scanned/
  image-only PDF has no text layer for `pypdf` to read).

## Known Limitations

- Only Anthropic is implemented as a live LLM provider; OpenAI/Gemini are stubbed to
  fall back to deterministic mode until implemented.
- The deterministic (no API key) fallback synthesizer and Requirement extractor are
  keyword-cue based - they work for *any* input, but at lower fidelity than the live
  LLM (e.g. a business problem with no matching cue words gets generic field names
  like `name`/`value`/`status` instead of domain-specific ones). This is expected, not
  a bug: it's what keeps the whole pipeline runnable with zero external dependencies.
- The Executor's capability-gap detection is field-existence based (does the
  synthesized data have this field at all) — it can't detect subtler unsupported cases
  where a field exists but the *semantics* don't match what was asked.
- No authentication — acceptable for a self-serve public demo sandbox, not for handling
  sensitive customer data.
- Schema changes are applied via `Base.metadata.create_all()` (new tables only, no
  migration history) — fine for this MVP's tables; a schema that evolves further should
  move to Alembic.
- Mini-app actions (Approve / Flag for review) are simulated and persisted to
  PostgreSQL for audit purposes, but don't trigger any real external system (no actual
  email/Slack/CRM call) — consistent with the Tool Registry's "no arbitrary outbound
  calls" safety rule for this MVP.
- Uploaded `.docx`/`.pdf`/`.pptx` files are read as plain text only - tables/images
  inside a PDF or PowerPoint aren't extracted as structured data (a docx's own tables
  are, since `python-docx` exposes them directly). Uploaded `.csv`/`.xlsx` files are
  capped at 200 rows and any file at 5 MB, to keep a demo session responsive.
- The flowchart builder is intentionally free-form (not tied to the Tool Registry) -
  it can't guarantee the resulting workflow does exactly what the diagram shows, only
  that the diagram's steps and connections are passed as context to the same
  Requirement Agent a typed prompt would use.
- The `goal` field is truncated at 200 characters (a pre-existing limit that predates
  file import/flowchart); a long flowchart-derived description can visibly cut off
  mid-sentence in the result screen. Cosmetic only - the full untruncated text is what
  the Requirement Agent actually reasoned over.

## Recommended Next Improvements

- Stream intermediate agent/step events over Server-Sent Events instead of the
  client-side fixed-duration animation, once the Executor does real (slower) I/O.
- Add Alembic migrations once the schema needs to evolve beyond `create_all()`.
- Add a lead-capture step ("Request Full Solution") wired to a CRM, once product
  scope calls for it.
- Add OpenAI/Gemini `LLMProvider` implementations behind the existing abstraction.
- Broaden the deterministic (no API key) field-cue and record-label heuristics in
  `agents/requirement_agent.py` so fallback mode produces more domain-specific sample
  fields for a wider range of business problems, not just the ones with a keyword hit.
- Extract tables from PDFs/PowerPoint slides as structured data (currently text-only),
  and consider OCR for scanned/image-only PDFs.
- Offer an optional "tie shapes to Tool Registry actions" mode in the flowchart
  builder for customers who want a guaranteed-executable diagram rather than a
  free-form one that's interpreted as context.
