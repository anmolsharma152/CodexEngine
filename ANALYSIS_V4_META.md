# CodexEngine V4.0 — Meta-Analysis & Gap Report

Generated: 2026-06-14

Cross-referenced against: `README.md`, `ANALYSIS.md`, `CodexEngine V3 → V4 Handoff Document.pdf`

---

## Legend

| Icon | Meaning |
|------|---------|
| ✅ | Complete |
| ⚠️ | Partially implemented |
| ❌ | Not started |

---

## 1. Completed Items

| Item | Source | Notes |
|------|--------|-------|
| Intent Router (3-lane) | README, Handoff | Router classifies `direct_casual`, `direct_parametric`, `retrieval_required` using `llama-3.1-8b-instant` at temp 0.0 |
| Async LLM calls | ANALYSIS.md §B | All 5 nodes use `ainvoke`; no synchronous `invoke` remains |
| `asyncio.to_thread` for DB | ANALYSIS.md §B | Retriever wraps sync SQLAlchemy via `to_thread` |
| `thread_id` randomization | ANALYSIS.md §C | `crypto.randomUUID()` on mount + "New Chat" |
| SSE buffer + try-catch | ANALYSIS.md §C | `streamBuffer.split("\n\n")` + `JSON.parse` wrapped in try-catch |
| Document Upload API | ANALYSIS.md §3A | `/upload`, `/upload/temporal`, re-ingest, delete, list endpoints |
| `data/raw/` directory | ANALYSIS.md §D | Auto-created by `server.py` and `ingestion.py` |
| `.env.example` | ANALYSIS.md §2B | Documents all 5 env vars |
| `docker-compose.yml` | ANALYSIS.md §2B | pgvector + backend + frontend with correct Docker env links |
| `Dockerfile` + `render.yaml` | ANALYSIS.md §2B | Container builds and Render deployment config |
| Structured Evaluator | Handoff Phase 1 Task 2 | Returns JSON with `relevant`, `sufficient`, `grounded`, `confidence`, `retry_needed` |
| Retrieval Thresholding | Handoff Phase 1 Task 1 | `SIMILARITY_THRESHOLD = 0.35` discards low-quality matches |
| Multi-format ingestion | Handoff Phase 4 | PDF (page-aware via PyMuPDF), CSV (row-aware via DictReader), TXT/MD, fallback |
| Compact citations | User feedback | `[p. 55]`, `[r. 3]`, `[doc]` — no verbose `[Source: ...]` |
| Provenance Clause | User feedback | Only cites context when fact came from it; no false `[Source: Internal AI Knowledge]` tag |
| Test suite ported | ANALYSIS.md §A | Both tests use `server.create_graph`, `user_query`/`search_query` keys, `response` output |
| Auth (JWT + bcrypt) | — | Register, login, thread ownership verification, token expiry |
| Multi-tenant isolation | — | `user_id` and `thread_id` scoped in metadata SQL; temporal document isolation |
| Citation drawer in UI | README | `handleCitationClick` + sliding context drawer with source text |
| Cognition Panel in UI | README | Shows intent, relevance, sufficiency, groundedness, confidence per response |
| 5 golden queries + eval harness | Handoff | `eval/golden_queries.json`, baseline + V2 + V2.5 + V4 result files |
| RAGAS evaluation | — | `eval/ragas_eval.py` computes faithfulness, answer relevancy, context precision/recall |

---

## 2. Partially Complete

| Item | Source | What's Done | What's Missing |
|------|--------|-------------|----------------|
| Async DB layer | ANALYSIS.md §B | Retriever uses `to_thread` for SQLAlchemy | `server.py` still uses synchronous `create_engine` for auth/threads/doc CRUD; `ingestion.py` is fully synchronous |
| Routing Philosophy | Handoff Phase 1 Task 3 | 3-lane intent classifier (casual, parametric, retrieval) | No "Retrieval Necessity Estimation" (RNE) — routing is hard classification, not a nuanced confidence-based estimator |
| Actor Relevance Logic | Handoff Phase 1 Task 4 | Evaluator runs before Actor and provides structured scores | Actor still has `is_sufficient` logic and decides what to do with context; evaluator doesn't fully own retrieval arbitration |
| Evaluation Harness | Handoff Phase 3 Task 9 | 5 golden queries, baseline + V2 + V2.5 + V4 comparisons, RAGAS scores | No retrieval precision metrics, no hallucination detection, no latency benchmarks, no regression CI |
| Multi-format chunkers | Handoff Phase 4 | PDF (page-aware), CSV (row-aware), TXT/MD | No SectionChunker, HeadingChunker, TableChunker, CodeChunker as described in the handoff |
| Frontend State Mgmt | ANALYSIS.md §2B | Auth, thread list, session files, document manager all work | No Zustand/React Context; calls backend directly from client component |

---

## 3. Not Started

| Item | Source | Why It Matters |
|------|--------|----------------|
| Autonomous Web Search | ANALYSIS.md §3A, Handoff | No Tavily/DDG/SerpAPI fallback when local context scores 0.0. System says "no relevant documents" instead of performing a live search |
| Cross-Encoder Re-ranking | ANALYSIS.md §3A, Handoff Phase 2 Task 5 | Retrieves top-5 by cosine similarity only. No secondary `ms-marco-MiniLM` reranking. This is the gold standard for production RAG quality |
| Hybrid Retrieval (BM25) | Handoff Phase 2 Task 6 | Vector-only search. No keyword/BM25 fallback for exact term matching, acronyms, APIs, or technical documentation |
| CI/CD Benchmarking | ANALYSIS.md §3A, Handoff Phase 3 | No `.github/workflows/eval.yml`. Evaluation requires manual `python tests/test_rigorous.py` |
| Tracing (LangSmith/OTel) | Handoff Phase 3 Task 8 | No node execution traces, no latency tracking, no token usage monitoring |
| Ingestion Tracking | Handoff Phase 4 | No document hashes, no `is_document_ingested()` check, no deduplication, no versioning, no lifecycle management |
| Structured Logging | ANALYSIS.md §2B | Every file uses `print()`. No `logging` module, no log levels, no structured output to files or external sinks |
| Rate Limiting | — | No request throttling on any API endpoint |

---

## 4. Code Quality Issues

| Issue | File(s) | Impact |
|-------|---------|--------|
| `Condenser` instantiates `ChatGroq` inside the function | `backend/src/nodes/condenser.py:23` | Every call re-instantiates the model; should be module-level like all other nodes |
| `GROQ_MODEL_NAME` env var documented but never read | `backend/.env.example` vs all node files | Models are hardcoded; cannot swap models without editing source code |
| `render.yaml` has `ALLOWED_ORIGINS: "*"` | `render.yaml:15` | Security concern for production; should target the actual Vercel deployment URL |
| DB schema seeded on every startup | `backend/server.py:64` | `create_auth_tables()` runs on every `import`, not just first boot |
| All logging uses `print()` | All backend files | No `logging` module, no log levels, no structured output |
| AGENTS.md warns about Next.js 16 breaking changes | `codex-ui/AGENTS.md` | UI code may break if it relies on deprecated Next.js conventions |

---

## 5. Immediate Next Steps (Priority Order)

1. **Cross-Encoder Re-ranking** — Add a `ms-marco-MiniLM` reranker between the vector retriever and the evaluator to improve context quality
2. **Web Search Fallback** — Integrate Tavily or DuckDuckGo for queries with no local match
3. **Hybrid Retrieval (BM25 + Vector)** — Combine keyword and vector search for better coverage
4. **CI/CD Pipeline** — Add `.github/workflows/eval.yml` to run golden queries + RAGAS on every push
5. **Tracing** — Wire up LangSmith or OpenTelemetry for node-level observability
6. **Structured Logging** — Replace all `print()` with `logging` module calls
7. **Async DB Driver** — Migrate remaining sync SQLAlchemy calls to `asyncpg` / `AsyncConnectionPool`
