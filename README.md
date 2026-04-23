# SentinelFlow

Production-style multi-agent operations system for automating business workflows with LLM-powered routing, layered memory, human review controls, and real-world integrations.

## Overview

SentinelFlow turns operational requests into executable workflows. Instead of acting like a chatbot, it behaves like an ops automation platform:

- Ingests support, onboarding, internal ops, and follow-up tasks
- Classifies and routes each task through cooperating agents
- Executes tool actions through modular integrations and webhooks
- Verifies outcomes before completion
- Stores persistent, episodic, and semantic memory for retrieval
- Learns from feedback, overrides, failures, and reliability signals over time

The project is intentionally structured as a resume-ready full-stack system rather than a single-page demo. It includes a FastAPI backend, React dashboard, PostgreSQL + pgvector memory layer, Redis-backed worker queue, Dockerized local environment, seeded data, and a polished UI for recruiter-friendly walkthroughs.

## Tagline

**SentinelFlow**  
Multi-agent workflow orchestration for modern operations teams.

## Architecture

```mermaid
flowchart LR
    A["Task Intake<br/>Dashboard / API / Zapier"] --> B["FastAPI API Layer"]
    B --> C["Redis Queue"]
    C --> D["Workflow Pipeline Worker"]
    D --> E["Decision Agent"]
    E --> F["Execution Agent"]
    F --> G["Verifier Agent"]
    G --> H["Feedback Agent"]
    E --> I["Semantic Memory<br/>pgvector retrieval"]
    H --> I
    D --> J["PostgreSQL<br/>tasks, workflows, traces, feedback"]
    F --> K["Tools / Integrations<br/>internal API, email simulation, Zapier"]
    B --> L["React Dashboard"]
    J --> L
```

## Agent Workflow

SentinelFlow processes work through a shared-state pipeline:

1. Task ingestion
2. Classification and routing by the Decision Agent
3. Tool execution by the Execution Agent
4. Quality review by the Verifier Agent
5. Completion or handoff to human review
6. Feedback logging and memory updates for future runs

Execution modes:

- `manual`: always pauses for human approval before execution
- `semi_autonomous`: auto-executes only above confidence thresholds
- `autonomous`: executes immediately unless confidence or verification rules force review

## Layered Memory

SentinelFlow implements three memory layers:

- **Persistent memory**: PostgreSQL tables store tasks, workflows, decisions, verifier results, feedback, integrations, and agent state snapshots.
- **Episodic memory**: execution logs, review decisions, overrides, failures, and end-to-end workflow traces preserve what happened during each run.
- **Semantic memory**: pgvector embeddings store task and outcome memories so the decision layer can retrieve similar past workflows and reuse successful patterns.

This combination lets the system compound operational intelligence over time instead of handling each task in isolation.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, LangChain, OpenAI API, RQ worker
- Frontend: React, Vite, React Query, Recharts
- Database: PostgreSQL
- Vector memory: pgvector
- Queue / async workflow: Redis
- Integrations: Zapier webhook support, internal API simulation, email simulation
- Infra: Docker, docker-compose, `.env` configuration

## Key Features

- Multi-agent workflow engine with explicit decision, execution, verification, and feedback stages
- Human-in-the-loop approval flow with manual, semi-autonomous, and autonomous modes
- Shared structured workflow context persisted across stages
- Retrieval-augmented decision support using semantic memory from prior runs
- Operational analytics dashboard with status counts, trends, trace stream, and time saved metrics
- Review queue for low-confidence or verifier-flagged workflows
- Modular tool registry for adding more integrations later
- Seeded example workflows for instant portfolio demos
- Deterministic fallback behavior when no OpenAI API key is provided

## Recommended Folder Structure

```text
SentinelFlow/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── orchestration/
│   │   ├── schemas/
│   │   ├── seed/
│   │   ├── services/
│   │   └── tools/
│   ├── scripts/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── styles/
│   │   └── utils/
│   ├── Dockerfile
│   └── package.json
├── infra/postgres/init/
├── docs/screenshots/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Product Walkthrough

The screenshots below show how a workflow moves through SentinelFlow from intake to monitoring, review, integrations, and API control.

### 1. Demo Lab: submit a new workflow

![Demo Lab](docs/screenshots/demo-lab.png)

This is the intake surface where an operator submits a new support, onboarding, internal ops, or follow-up request.  
Once submitted, the task is sent to the FastAPI backend, persisted in PostgreSQL, and queued for agent processing through Redis.

### 2. Workflow Inventory: track active and completed runs

![Workflow Inventory](docs/screenshots/workflows.png)

This page shows the live workflow table with task type, execution mode, confidence, latency, and current status.  
It acts as the main command center for inspecting how the Decision, Execution, and Verifier agents are handling requests.

### 3. Human Review Queue: handle low-confidence or flagged tasks

![Review Queue](docs/screenshots/review-queue.png)

If a workflow has low confidence or fails verification, SentinelFlow routes it here instead of auto-completing it.  
Operators can approve, reject, or override decisions so the system stays reliable while still automating most of the workload.

### 4. Dashboard: monitor system performance and workflow outcomes

![Dashboard](docs/screenshots/dashboard.png)

The dashboard gives a recruiter-friendly view of total workflows processed, time saved, latency, status mix, and recent decisions.  
It makes the platform easy to explain as an operational system rather than just an LLM demo.

### 5. Integrations Console: configure external tools and webhooks

![Integrations](docs/screenshots/integrations.png)

This screen manages the execution layer by showing internal APIs, notification tools, and Zapier webhook connectivity.  
It demonstrates that the system is designed to take real actions through tools, not just classify or summarize work.

### 6. FastAPI API Docs: inspect and test the backend surface

![FastAPI Docs](docs/screenshots/fastapi-docs.png)

The backend exposes clean REST endpoints for tasks, workflows, review actions, analytics, integrations, and demo runs.  
These docs make the platform easy to test, extend, and discuss in interviews from a systems-design perspective.

## Backend Highlights

- `app/orchestration/pipeline.py`: shared-state workflow orchestration
- `app/agents/`: decision, execution, verifier, and feedback agent logic
- `app/services/memory_service.py`: semantic retrieval and embedding storage
- `app/services/policy_service.py`: feedback-driven prompt and policy hints
- `app/tools/`: modular tool-calling layer
- `app/api/routes/`: REST endpoints for tasks, analytics, review, demo runs, integrations, and webhooks

## Frontend Highlights

- Dashboard with recruiter-friendly operational metrics
- Workflow inventory with filtering and search
- Task detail page with full agent trace and memory/state visibility
- Review queue for approval and override decisions
- Integrations console for webhook configuration and testing
- Demo submission page for creating new workflows or generating a seeded demo suite

## Database Schema

Core tables:

- `tasks`
- `workflows`
- `agent_decisions`
- `execution_logs`
- `verifier_results`
- `feedback_events`
- `agent_states`
- `users`
- `integrations`
- `memory_embeddings`

Schema behavior:

- SQLAlchemy models define the application schema
- Postgres bootstrap enables the `vector` extension in `infra/postgres/init/001_extensions.sql`
- On startup, the backend creates tables and seeds demo data if the database is empty

## API Overview

Key endpoints:

- `POST /api/v1/tasks` create and optionally queue a workflow task
- `GET /api/v1/tasks` list tasks with status and type filters
- `GET /api/v1/tasks/{task_id}` view full workflow detail and trace
- `GET /api/v1/workflows/{workflow_id}` inspect workflow state snapshots
- `GET /api/v1/review/queue` list items awaiting human review
- `POST /api/v1/review/{task_id}/approve` approve or override a review item
- `POST /api/v1/review/{task_id}/reject` reject a review item
- `GET /api/v1/analytics/overview` load dashboard metrics and trace stream
- `GET /api/v1/integrations` list integration settings
- `PUT /api/v1/integrations/{integration_id}` update integration configuration
- `POST /api/v1/integrations/{integration_id}/test` run a connectivity check
- `POST /api/v1/demo/run` generate demo workflows
- `POST /api/v1/webhooks/zapier` ingest tasks from a Zapier-style webhook

## Environment Variables

Root `.env` for Docker:

```env
POSTGRES_DB=sentinelflow
POSTGRES_USER=sentinel
POSTGRES_PASSWORD=sentinel
DATABASE_URL=postgresql+psycopg://sentinel:sentinel@postgres:5432/sentinelflow
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
AUTO_APPROVAL_THRESHOLD=0.78
VERIFIER_PASS_THRESHOLD=0.8
DEFAULT_ZAPIER_WEBHOOK_URL=
APP_ENV=development
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Local development examples:

- `backend/.env.example` uses `localhost` services
- `frontend/.env.example` points the UI at the backend API

## Local Development

### 1. Start PostgreSQL and Redis

```bash
docker compose up -d postgres redis
```

### 2. Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Run the worker

```bash
cd backend
source .venv/bin/activate
python -m app.worker
```

### 4. Run the frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend: [http://localhost:3000](http://localhost:3000)  
Backend API: [http://localhost:8000](http://localhost:8000)

## Docker Run

### 1. Copy the root environment file

```bash
cp .env.example .env
```

### 2. Start the full stack

```bash
docker compose up --build
```

Services:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

## Demo Workflow Walkthrough

Typical demo flow:

1. Open the Demo Lab and submit a support or onboarding task
2. The API writes the task and workflow state to PostgreSQL
3. Redis queues the workflow for the worker
4. The Decision Agent retrieves similar memories and selects an action plan
5. The Execution Agent calls the tool registry and configured integrations
6. The Verifier Agent validates the result
7. SentinelFlow either completes the workflow or routes it to human review
8. Feedback and embeddings are recorded for future retrieval

## Seeded Sample Data

The first startup seeds representative workflows:

- Completed support triage flow
- Completed onboarding flow
- Internal ops request waiting for manual approval
- Follow-up automation flagged by the verifier for review

This makes the dashboard, review queue, and detail views demo-ready immediately.

## Real Integrations and Mock Boundaries

Implemented as real extension points:

- Redis-backed background processing
- Zapier-style webhook ingestion and outbound webhook emission
- OpenAI + LangChain integration hooks
- pgvector semantic retrieval

Simulated but replaceable:

- Internal API tool responses
- Email delivery behavior
- Some fallback decision logic when OpenAI credentials are not configured

The code intentionally keeps these boundaries modular so real services can replace simulations with minimal refactoring.

## Commands

Backend:

```bash
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Worker:

```bash
cd backend && python -m app.worker
```

Frontend:

```bash
cd frontend && npm run dev
```

Full stack:

```bash
docker compose up --build
```

## Future Deployment

Recommended next steps for deployment:

- Put FastAPI behind a production ASGI server and reverse proxy
- Serve the React build from a CDN or edge cache
- Use managed PostgreSQL with pgvector enabled
- Use managed Redis for queue durability
- Move secrets into a cloud secret manager
- Replace email simulation and internal API mocks with real SaaS integrations
- Add background retry policies, dead-letter handling, and alerting

## Future Improvements

- Real authentication and role-based operator access
- Workflow templates editable from the UI
- Vector index tuning and larger memory corpora
- Prompt/version registry for safer learning loops
- More granular execution step retries and compensating actions
- SLA breach forecasting and richer incident analytics
- Audit-grade approval logs and compliance exports

## Resume-Ready Impact Summary

SentinelFlow demonstrates:

- End-to-end agentic workflow orchestration across backend, worker, database, and UI
- Practical multi-tier memory using relational state, traces, and vector retrieval
- Human-in-the-loop reliability patterns for low-confidence automation
- Production-inspired system design with queues, integrations, observability, and Dockerized local infra
- Strong portfolio storytelling around business automation, operational leverage, and applied AI systems

## How This Maps to Agentic Systems

- **Agentic systems**: multiple specialized agents make decisions, take actions, verify outcomes, and hand off work.
- **Multi-tier memory**: persistent rows, episodic traces, and semantic retrieval all shape future behavior.
- **Shared state**: the workflow context is stored and evolved across every pipeline stage.
- **Feedback loops**: success, failures, overrides, confidence, and latency are recorded as learning signals.
- **Compounding intelligence over time**: new tasks benefit from similar historical outcomes, policy hints, and reliability patterns captured from previous runs.
