# CodexEngine V4.0 — Meta-Analysis & Gap Report

Generated: 2026-06-19

Cross-referenced against: `README.md`, `server.py`, `src/`, `Project Overview CodexEngine.txt`

---

## Legend

| Icon | Meaning |
|------|---------|
| ✅ | Complete |
| ⚠️ | Partially implemented |
| ❌ | Not started |

---

## 1. Completed Items

| Item | Location | Notes |
|------|----------|-------|
| Intent Router (3-lane) | `src/nodes/router.py` | Classifies `direct_casual`, `direct_parametric`, `retrieval_required` |
| Async LLM calls | All nodes | All 5 nodes use `ainvoke`; no synchronous `invoke` |
| Async DB wrappers | `src/nodes/retriever.py` | Sync SQLAlchemy wrapped via `asyncio.to_thread` |
| SSE streaming | `server.py` | Chat endpoint streams via Server-Sent Events |
| Document Upload API | `server.py` | `/upload`, `/upload/temporal`, re-ingest, delete, list |
| Structured Evaluator | `src/nodes/evaluator.py` | Returns JSON with `relevant`, `sufficient`, `grounded`, `confidence`, `retry_needed` |
| Retrieval Thresholding | `src/nodes/retriever.py:14` | `SIMILARITY_THRESHOLD = 0.35` discards low-quality matches |
| Multi-format ingestion | `scripts/ingestion.py` | PDF (PyMuPDF page-aware), CSV (row-aware), TXT/MD |
| Compact citations | Actor prompt + UI | `[p. X]`, `[r. X]`, `[doc]`, `[web]` — no verbose tags |
| Provenance clause | Actor prompt | Only cites context when fact came from it |
| Auth (Supabase) | `server.py` + `src/supabase_client.py` | Register, login, JWT validation, thread ownership |
| Multi-tenant isolation | `src/nodes/retriever.py` | `user_id` + `thread_id` scoped in metadata SQL |
| Citation drawer | Frontend | `handleCitationClick` + sliding context panel |
| Cognition Panel | Frontend | Shows intent, relevance, sufficiency, groundedness, confidence |
| 5 golden queries + eval harness | `eval/golden_queries.json` | Baseline + V2 + V2.5 + V4 result files |
| RAGAS evaluation | `eval/ragas_eval.py` | Faithfulness, answer relevancy, context precision/recall |
| Hybrid retrieval (BM25 + vector) | `src/nodes/retriever.py` | Both searches run, merged via score |
| Web search fallback | `src/nodes/retriever.py:92` | DuckDuckGo when local scores are low |
| Structured logging | `src/log_utils.py` | `logger.info/error/warning` used in all nodes, server, ingestion, eval |
| Test suite | `tests/test_golden.py`, `tests/test_rigorous.py` | CI-configured, uses local pgvector |
| CI pipeline | `.github/workflows/eval.yml` | Runs golden + rigorous + RAGAS on push to main |
| Supabase auth + storage | `server.py` | JWT via `supabase.auth.get_user()`, files via `supabase.storage` |
| Database schema | `server.py:ensure_schema()` + `supabase/seed.sql` | Auto-creates vector ext, threads table, prose_chunks table |
| Embedding model | `src/repositories/utils.py` | Google Gemini `models/gemini-embedding-001` via API (384d via `output_dimensionality`). Replaced local ONNX (`fastembed`) to fit Render 512MB. Falls back to BM25-only if API unreachable. |

---

## 2. Partially Complete

| Item | What's Done | What's Missing |
|------|-------------|----------------|
| Cross-encoder re-ranking | Disabled — removed to keep container under 512MB (Render free tier) | Was never fully wired; fallback to score-based sort works fine |
| GROQ_MODEL_NAME env var | `src/llm.py` reads it via `os.getenv()` | `actor.py:7` hardcodes `llama-3.3-70b-versatile` instead of using the env var |
| DB schema initialization | `ensure_schema()` runs on every startup | Should only run on first boot, not on every import |
| Frontend state management | Auth, threads, documents all work | No Zustand/React Context — calls backend directly from client component |
| Multi-format chunkers | PDF (page-aware), CSV (row-aware), TXT/MD | No SectionChunker, HeadingChunker, TableChunker, CodeChunker |
| Evaluation harness | Golden queries + RAGAS + CI | No retrieval precision metrics, no hallucination detection, no latency benchmarks |

---

## 3. Not Started

| Item | Why It Matters |
|------|----------------|
| RLS Policies on Supabase | Added to `supabase/seed.sql` — storage.objects policies restrict users to their own `user_id/` folder prefix |
| Ingestion deduplication | No document hashes, no `is_document_ingested()` check, no versioning |
| Rate limiting | No request throttling on any endpoint |
| Async DB driver | `server.py` still uses synchronous `create_engine` for threads/docs CRUD |
| Tracing (LangSmith/OTel) | No node execution traces, no latency tracking, no token usage monitoring |

---

## 4. Code Quality Issues

| Issue | File(s) | Impact |
|-------|---------|--------|
| `Condenser` instantiates `ChatGroq` inside function | `src/nodes/condenser.py:23` | Re-instantiates model every call; should be module-level |
| `ALLOWED_ORIGINS` set to Vercel URL | `render.yaml` | Updated to `https://codex-engine.vercel.app` (or set via env var) |
| `ingestion.py` fully synchronous | `scripts/ingestion.py` | Blocks async event loop when called from upload endpoints |
| `data/raw/` directory stale | `codex-backend/data/raw/` | 12 old PDFs remain from pre-Supabase ingestion; no longer used |

---

## 5. Deployment State

| Service | Status | Config | Notes |
|---------|--------|--------|-------|
| Render (backend) | ❌ Not deployed | `render.yaml` exists, `sync: false` for all secrets | Needs manual env var setup in dashboard |
| Vercel (frontend) | ❌ Not deployed | `vercel.json` exists | Needs `NEXT_PUBLIC_*` env vars set |
| Supabase (auth, storage, DB) | ❌ Not set up | `seed.sql` + bucket name configured in code | Needs project creation in browser |
| GitHub CI | ✅ Passing | Dummy Supabase vars + `GROQ_API_KEY` secret | Real Supabase secrets can be added later |
| Local Arch PostgreSQL | ✅ Running | Port 5432, DB `codex_db`, user `anmol` | Used for RAG vector data in dev |
| Docker PostgreSQL | ❌ Not running | Defined in `docker-compose.yml` | Conflicts with Arch pg on port 5432 |

### Environment Variables Required

| Variable | Where | Status |
|----------|-------|--------|
| `GROQ_API_KEY` | Root `.env`, `codex-backend/.env` | ✅ Present (gitignored) |
| `DB_URL` | Root `.env`, `codex-backend/.env` | ✅ Present (points to Arch pg) |
| `SUPABASE_URL` | `codex-backend/.env` | ❌ Missing |
| `SUPABASE_ANON_KEY` | `codex-backend/.env` | ❌ Missing |
| `NEXT_PUBLIC_SUPABASE_URL` | `codex-frontend/.env.local` | ❌ Missing |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `codex-frontend/.env.local` | ❌ Missing |
| `NEXT_PUBLIC_API_URL` | `codex-frontend/.env.local` | ❌ Missing |

---

## 6. Database Options

The project supports three PostgreSQL backends:

| Option | Setup | Use Case |
|--------|-------|----------|
| **Arch native PostgreSQL** | Arch package `postgresql` + `pgvector` AUR. Running on port 5432. | Development (current) |
| **Docker pgvector** | `docker compose up -d db` from repo root. Container on port 5432. | CI / reproducible dev |
| **Supabase Postgres** | Cloud-hosted Postgres with pgvector. Connection string from Supabase dashboard. | Production / deployment |

**Conflict note:** Arch native pg and Docker pgvector both listen on port 5432. Only one should run at a time.

---

## 7. API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Create account (via Supabase Auth) |
| POST | `/login` | No | Get JWT token (via Supabase Auth) |
| GET | `/user/me` | Yes | Current user info |
| GET | `/threads` | Yes | List threads |
| POST | `/threads` | Yes | Create/update thread |
| DELETE | `/threads/{id}` | Yes | Delete thread + associated data |
| POST | `/chat/stream` | Yes | SSE streaming chat |
| GET | `/chat/{id}/history` | Yes | Message history |
| POST | `/upload` | Yes | Ingest document (to Supabase Storage) |
| POST | `/upload/temporal` | Yes | Session-scoped upload |
| GET | `/documents` | Yes | List documents |
| DELETE | `/documents/{filename}` | Yes | Delete document |
| POST | `/documents/{filename}/reingest` | Yes | Re-ingest document |
| DELETE | `/chat/{thread_id}/temporal` | Yes | Clear temporal chunks |

---

## 8. Immediate Next Steps (Priority Order)

1. **Create Supabase project** — Needed for auth + storage to work
2. **Deploy backend to Render** — Connect repo, set env vars
3. **Deploy frontend to Vercel** — Connect repo, set NEXT_PUBLIC_* vars
4. **Enable RLS on Supabase tables** — Run RLS policies in SQL Editor
5. **Wire cross-encoder reranker** — Connect `get_reranker()` into retrieval pipeline
6. **Clean up stale `data/raw/`** — Remove old PDFs or migrate to Supabase Storage
7. **Add async DB driver** — Replace sync `create_engine` with `asyncpg` for threads/docs CRUD
