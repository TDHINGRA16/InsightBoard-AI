# InsightBoard AI

InsightBoard AI is a transcript-to-task dependency engine. Upload a project transcript, extract tasks + dependencies using an LLM, persist the resulting graph, and visualize it as an interactive node graph.

## Level Completed

**Level 3 (Levels 1–3 completed).**

## LLM API + Tech Stack

### LLM API

- **Groq API** (via the `groq` Python SDK). The model is configured through `GROQ_MODEL` (default: `llama-3.3-70b-versatile`).

### Frontend

- **Next.js 15** (App Router) + **React 19** + **TypeScript**
- **Bun** (lockfile + Docker build uses Bun)
- **Tailwind CSS** + Radix UI primitives
- **React Query** (TanStack Query) for client caching/mutations
- **React Flow** for dependency graph visualization
- **Supabase Auth** (JWT-based auth in the UI)

### Backend

- **FastAPI (Python)** + **Uvicorn/Gunicorn**
- **SQLAlchemy** + **PostgreSQL**
- **Redis** for caching + job queue backend
- **RQ (Redis Queue)** for background workers (async analysis/export jobs)
- **NetworkX** for graph validation and algorithms (cycle detection, DAG checks, critical path)

### Deployment

- **Docker** (separate `frontend/Dockerfile` and `backend/Dockerfile`).

## Cycle Detection Algorithm (Level 1/Integrity Requirement)

Cycle detection is implemented using NetworkX on a directed graph built from stored tasks and dependencies:

- The backend constructs a `DiGraph` from tasks (nodes) and dependencies (edges).
- It checks DAG validity using `nx.is_directed_acyclic_graph(graph)`.
- If the graph is not a DAG, it extracts a cycle using `nx.simple_cycles(graph)` and returns the first detected cycle.

Behavior on cycle detection:

- The analysis job **does not crash**.
- Tasks participating in the detected cycle are **persisted as** `status = blocked` in the database.
- The analysis response payload includes diagnostics such as `cycle`, `cycle_task_ids`, and `blocked_task_count`.

Key references:

- DAG validation and cycle extraction: `backend/app/services/dependency_service.py` (`validate_dag`)
- Persist + response diagnostics: `backend/app/workers/tasks.py` (`analyze_transcript_job`)

## Idempotency Logic (Level 2 — Async + Duplicate Cost Prevention)

This project implements idempotency at two layers:

### 1) Transcript upload deduplication (content-based)

- On upload, the backend computes `SHA-256(content)` and stores it as `content_hash`.
- If a transcript with the same `content_hash` already exists, the API returns the existing transcript instead of creating a new row.

Reference:

- `backend/app/services/transcript_service.py` (`upload_transcript`)

### 2) Analysis job idempotency (request-key based)

- `POST /api/v1/analysis/start` requires an `idempotency_key`.
- If a job with the same `idempotency_key` exists:
  - **QUEUED/PROCESSING** → return the existing `job_id` (true idempotency).
  - **COMPLETED/FAILED** and `force=false` → return the existing job/result (no re-run).
  - **COMPLETED/FAILED** and `force=true` → delete old tasks/dependencies and start a fresh analysis run.

References:

- API flow: `backend/app/api/v1/analysis.py` (`start_analysis`)
- Job key lookup helpers: `backend/app/utils/idempotency.py`

## Local Setup (Run Locally)

### Prerequisites

- **Node/Bun**: Bun recommended (repo includes `frontend/bun.lock`)
- **Python 3.11+**
- **PostgreSQL**
- **Redis**

### 1) Backend (FastAPI)

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Create `backend/.env` (the backend loads `.env` automatically) with at least:

- `DATABASE_URL` (Postgres connection string)
- `REDIS_URL` (Redis connection string)
- `GROQ_API_KEY`
- `GROQ_MODEL` (optional; defaults to `llama-3.3-70b-versatile`)
- `SUPABASE_URL` (optional for local)
- `SUPABASE_JWT_SECRET` (local/dev default exists, but set your real secret for production)

4. Run the API:

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Run a worker (required for async analysis jobs):

- **Windows** (recommended):

```bash
cd backend
python run_worker.py
```

- **Linux/macOS**:

```bash
cd backend
rq worker --url "$REDIS_URL" high default low
```

The backend health endpoint is available at `http://localhost:8000/health`.

### 2) Frontend (Next.js)

1. Install dependencies:

```bash
cd frontend
bun install
```

2. Create `frontend/.env.local` with:

- `NEXT_PUBLIC_API_URL` (example: `http://localhost:8000/api/v1`)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

3. Start the dev server:

```bash
cd frontend
bun dev
```

Open `http://localhost:3000`.

## Notes

- The backend stores transcripts, tasks, dependencies, and the computed graph (React Flow-compatible) in the database.
- The frontend graph view supports instant “unlocking” of dependent tasks via optimistic UI updates after completing a task, without a full page refresh.

