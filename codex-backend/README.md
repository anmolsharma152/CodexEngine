# CodexEngine Backend

FastAPI server powering the v5 workspace agent.

---

## Folder Structure

```
codex-backend/
├── server.py                 # FastAPI app, auth, endpoints, SSE streaming
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container build (python:3.12-slim)
├── .env.example              # Required env vars template
├── src/
│   ├── agent/
│   │   ├── agent_loop.py     # While-true agent loop (LLM → tools → loop)
│   │   ├── tool_registry.py  # @tool decorator + ToolRegistry singleton
│   │   └── tools.py          # 5 installed tools
│   ├── llm/
│   │   ├── __init__.py       # create_provider factory
│   │   └── providers.py      # LLMProvider base + OpenAICompatible adapter
│   ├── db.py                 # Sync + async engines, schema creation (5 tables)
│   ├── log_utils.py          # Logging config
│   ├── repositories/
│   │   └── utils.py          # Embedding function, BM25 index, reranker
│   ├── storage_client.py     # Supabase Storage (upload/download/list/remove)
│   └── supabase_client.py    # Supabase auth client
├── scripts/
│   └── ingestion.py          # File ingestion: text extraction → chunking → embedding → DB
├── tests/
│   ├── test_golden.py        # v4-era test (imports LangGraph — broken on agentic)
│   └── test_rigorous.py      # v4-era evaluation suite (broken on agentic)
├── docs/
│   ├── workspace-experiment.md
│   ├── project-isolation-validation.md
│   ├── dogfooding-checklist.md
│   └── future-memory-model.md
├── eval/
│   ├── golden_queries.json   # Golden test queries
│   └── ragas_eval.py         # RAGAS evaluation script
├── data/                     # Local file storage (gitignored)
└── supabase/                 # Supabase config/migrations
```

---

## Agent Loop

`src/agent/agent_loop.py` — the core execution engine.

A while-true loop with plain dict messages. No LangGraph, no DAG, no state machine.

```
User Message
     │
     ▼
┌──────────────────────────────┐
│     Flexible Agent Loop      │
│                              │
│  LLM decides per-turn:       │
│                              │
│  ┌──────────────────────┐    │
│  │ tool_call(s) → exec  │───→│ loop (multi-step)
│  │ respond       → emit │───→│ done
│  └──────────────────────┘    │
└──────────────────────────────┘
```

At each iteration the LLM either calls one or more tools (results appended to context, loop continues) or produces a final response (streamed to user, loop exits). A `MAX_ITERATIONS` guard prevents infinite loops.

The active `project_id` is injected into workspace tool calls (`read_document`, `write_document`, `list_documents`) programmatically — the LLM never decides which project to operate in.

---

## Tool Registry

`src/agent/tool_registry.py` — `@tool` decorator + `ToolRegistry` singleton.

The `@tool` decorator auto-generates a JSON schema from each function's type hints, defaults, and docstring. Schemas are sent to the LLM as `tools` parameter in the API call. The `ToolRegistry` stores function references and executes them by name during the agent loop.

Supports sync and async functions. Thread-safe.

Usage:
```python
from src.agent.tool_registry import tool

@tool
async def search_documents(query: str, top_k: int = 5) -> str:
    """Search uploaded documents..."""
    ...
```

---

## Current Tools

| Tool | File | Description |
|---|---|---|
| `search_documents` | `src/agent/tools.py:110` | Hybrid vector + BM25 search across uploaded documents. Threshold: 0.35 similarity. Top-K: 10 vector + 10 BM25 → rerank → 5 final. |
| `search_web` | `src/agent/tools.py:137` | DuckDuckGo text search. Returns up to 3 snippet results. |
| `read_document` | `src/agent/tools.py:159` | Full text of a workspace artifact by path + project_id. |
| `write_document` | `src/agent/tools.py:175` | Create or overwrite a workspace artifact. Upserts on `(project_id, path)` UNIQUE constraint. |
| `list_documents` | `src/agent/tools.py:195` | List artifacts in a project, optionally filtered by SQL LIKE pattern. |

---

## Database Tables

All tables are created by `src/db.py:ensure_schema()`.

| Table | Purpose | Key Columns |
|---|---|---|
| `threads` | Chat thread metadata | `id`, `user_id`, `title`, `timestamp`, `pinned` |
| `chat_messages` | Message history per thread | `id`, `thread_id`, `user_id`, `role`, `content`, `created_at` |
| `prose_chunks` | Document chunks with embeddings | `id`, `content`, `metadata` (JSONB), `embedding` (vector(384)) |
| `workspace_artifacts` | Persistent agent artifacts | `id`, `project_id`, `path`, `content`, `artifact_type` — UNIQUE `(project_id, path)` |
| `tool_invocations` | Tool call log | `id`, `thread_id`, `user_id`, `tool_name`, `arguments`, `result`, `error`, `duration_ms` |

---

## Ingestion Pipeline

`scripts/ingestion.py` — called after file upload.

```
Upload → Supabase Storage → Download temp → Extract text (pymupdf for PDFs)
→ RecursiveCharacterTextSplitter (1024 chunk, 200 overlap) → Embed (fastembed
bge-small-en-v1.5, 384-dim) → Store in prose_chunks table
```

The pipeline runs synchronously in a thread pool (`asyncio.to_thread`). Supports PDF files. Metadata includes `source`, `page`, `user_id`, and optional `thread_id`.

---

## API Entrypoints

All endpoints in `server.py`. Auth via Bearer JWT from Supabase.

| Method | Path | Description |
|---|---|---|
| POST | `/register` | Create account (rate-limited: 10/min per IP) |
| POST | `/login` | Sign in, returns JWT |
| GET | `/user/me` | Current user profile |
| GET | `/threads` | List user's threads |
| POST | `/threads` | Save/update thread |
| DELETE | `/threads/{id}` | Delete thread + chunks |
| POST | `/chat/stream` | SSE streaming chat (rate-limited: 8/min per user) |
| GET | `/chat/{id}/history` | Message history for a thread |
| POST | `/upload` | Upload + ingest a document |
| GET | `/documents` | List uploaded documents with ingestion status |
| DELETE | `/documents/{filename}` | Delete document + chunks |
| POST | `/documents/{filename}/reingest` | Re-download + re-ingest |
| POST | `/upload/temporal` | Upload for a specific thread |
| DELETE | `/chat/{id}/temporal` | Delete thread-scoped chunks |
| GET | `/` | Health check |

---

## LLM Providers

`src/llm/providers.py` — abstract `LLMProvider` base with one concrete adapter.

`OpenAICompatible` works with any OpenAI-compatible API:
- Groq (`https://api.groq.com/openai/v1`)
- OpenAI (`https://api.openai.com/v1`)
- Together (`https://api.together.xyz/v1`)

Default models per provider are configured via env vars (`GROQ_MODEL_NAME`, `OPENAI_MODEL_NAME`, `TOGETHER_MODEL_NAME`). The agent selects a provider via the `ChatRequest.provider` field (default: `"groq"`).
