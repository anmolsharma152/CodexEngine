# CodexEngine V4.0 - Knowledge Operating System

Stateful, multi-agent RAG system with LangGraph orchestration, pgvector, Supabase auth/storage, and a Next.js glassmorphic UI.

## Architecture

```
User
  │
  ├──► Frontend (Next.js 16)
  │       │
  │       ├──► Supabase Auth (login/register)
  │       │
  │       └──► Backend API (FastAPI + SSE)
  │               │
  │               ├──► LangGraph Pipeline
  │               │     Router → Condenser → Retriever → Evaluator
  │               │     → Rewriter (loop ×3) → Actor → Response
  │               │
  │               ├──► PostgreSQL + pgvector (RAG data)
  │               │     (Arch native OR Docker OR Supabase Postgres)
  │               │
  │               └──► Supabase Storage (file uploads)
  │
  └──► Groq API (LLM inference)
```

### Embedding Model

Embeddings are produced via the **Google Gemini API** using `models/embedding-001` (384-dimensional output via `output_dimensionality`). This avoids running a heavy ONNX model locally, keeping the container small enough for Render's free tier (512MB RAM).

- **API key**: Get a free key at https://aistudio.google.com/app/apikey
- **Environment variable**: `GOOGLE_API_KEY`
- **On failure**: the retriever degrades to BM25-only search, so the system stays functional even if the embedding API is unreachable.

### Directory Structure

```
CodexEngine/
├── codex-backend/
│   ├── server.py              # FastAPI app (SSE streaming, auth, CRUD)
│   ├── src/
│   │   ├── state.py           # TypedDict AgentState schema
│   │   ├── log_utils.py       # Structured logging
│   │   ├── llm.py             # Centralized LLM init
│   │   ├── supabase_client.py # Supabase client singleton
│   │   ├── repositories/
│   │   │   └── utils.py       # Embedding (Gemini API) + BM25
│   │   └── nodes/
│   │       ├── router.py      # Intent classifier (3-lane)
│   │       ├── retriever.py   # Hybrid: vector + BM25 + web fallback
│   │       ├── evaluator.py   # Structured JSON evaluator
│   │       ├── rewriter.py    # Search query optimizer
│   │       ├── condenser.py   # Memory/history resolution
│   │       └── actor.py       # Response synthesis with provenance
│   ├── scripts/ingestion.py   # PDF/CSV/TXT ingestion
│   ├── tests/                 # test_golden.py, test_rigorous.py
│   ├── eval/                  # RAGAS eval, golden queries
│   ├── supabase/seed.sql      # Database schema
│   ├── Dockerfile
│   └── requirements.txt
├── codex-frontend/            # Next.js 16 + Tailwind
│   ├── app/page.tsx           # Main UI component
│   ├── vercel.json
│   └── Dockerfile
├── docker-compose.yml
├── render.yaml
└── .github/workflows/eval.yml
```

## Quick Start

### Prerequisites

- Python 3.12+ (or `uv` package manager)
- Node.js 20+
- PostgreSQL with pgvector extension (one of):
  - Arch Linux: `sudo pacman -S postgresql` + AUR `pgvector`
  - Docker: `docker compose up -d db` (runs `pgvector/pgvector:pg16`)
- A Supabase project (free tier) for auth and file storage
- A Groq API key (LLM inference)
- A Google API key (embeddings — free at https://aistudio.google.com/app/apikey)

### 1. Backend Setup

```bash
cd codex-backend

# Option A: using pip
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Option B: using uv
uv venv && uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys:
#   GROQ_API_KEY, DB_URL, SUPABASE_URL, SUPABASE_ANON_KEY, GOOGLE_API_KEY
```

### 2. Database

Pick one:

```bash
# Option A: Arch native PostgreSQL (already running on port 5432)
# Verify: pg_isready

# Option B: Docker pgvector container
docker compose up -d db       # runs pgvector on port 5432

# Option C: Supabase cloud Postgres
# Get connection string from Supabase dashboard → Settings → Database
# Update DB_URL in .env:
#   DB_URL="postgresql+psycopg://postgres:pass@db.xxx.supabase.co:5432/postgres?sslmode=require"
```

### 3. Start Backend

```bash
uvicorn server:app --reload --host 127.0.0.1 --port 8000
# or: uv run fastapi dev server.py
```

### 4. Frontend Setup

```bash
cd codex-frontend
npm install
# Create .env.local with:
#   NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
#   NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
#   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev
```

### 5. Create Supabase Bucket

In Supabase dashboard → Storage → Create bucket → name: `documents` (non-public).
Disable email confirmation in Auth → Providers → Email → toggle "Confirm email" OFF.

### 6. Run Database Schema

Run `codex-backend/supabase/seed.sql` in Supabase SQL Editor to create tables and RLS policies.

## Testing

```bash
cd codex-backend
source .venv/bin/activate
python tests/test_golden.py       # Single query
python tests/test_rigorous.py     # Full sweep
python eval/ragas_eval.py         # RAGAS metrics
```

## Deployment

| Service | Config | Env Vars |
|---------|--------|----------|
| Render (backend) | `render.yaml` | `DB_URL`, `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GOOGLE_API_KEY`, `ALLOWED_ORIGINS` |
| Vercel (frontend) | `vercel.json` | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL` |

### Deploy Steps

1. **Render**: Connect repo via Blueprint → set env vars → deploy
2. **Vercel**: Import repo, root dir `codex-frontend`, set env vars → deploy
3. **Supabase**: Run `codex-backend/supabase/seed.sql` in SQL Editor to create tables on the cloud DB
4. **Storage RLS**: The seed.sql includes policies; verify bucket `documents` exists (lowercase, non-public)
5. **After deploy**: Update `ALLOWED_ORIGINS` on Render to include `https://<your-vercel-app>.vercel.app`

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Create account |
| POST | `/login` | No | Get JWT token |
| GET | `/user/me` | Yes | Current user info |
| GET | `/threads` | Yes | List threads |
| POST | `/threads` | Yes | Create/update thread |
| DELETE | `/threads/{id}` | Yes | Delete thread |
| POST | `/chat/stream` | Yes | SSE streaming chat |
| GET | `/chat/{id}/history` | Yes | Message history |
| POST | `/upload` | Yes | Ingest document |
| POST | `/upload/temporal` | Yes | Session-scoped upload |
| GET | `/documents` | Yes | List documents |
| DELETE | `/documents/{filename}` | Yes | Delete document |
| POST | `/documents/{filename}/reingest` | Yes | Re-ingest document |
