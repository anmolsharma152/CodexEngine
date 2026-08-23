# CodexEngine: Latest Issues, Root Cause Analysis & Proposals (v4 & v5)

> **Document Status:** Architectural Synthesis & Action Plan  
> **Date:** August 2026  
> **Branches Covered:** `main` (v4 Stable LangGraph Engine) & `agentic` (v5 Experimental Workspace Agent)

---

## Executive Summary

This document captures the findings, debugging sessions, root-cause analyses, and proposed architectural improvements discussed across recent testing sessions for both the **v4 production branch (`main`)** and the **v5 experimental workspace agent branch (`agentic`)**.

No application code has been modified in this commit; this document serves as the single source of truth for upcoming implementation sessions.

---

## 1. Issue: Supabase 7-Day Inactivity Auto-Pause Warning

### 🔴 The Problem
Supabase issued an automated email warning that project `CodexEngine` (ID: `exwaglxsxdxcevpslecb`) is scheduled for auto-pausing due to zero detected activity over a 7-day period.

### 🔍 Root Cause
- **Render is kept awake by UptimeRobot**, which pings `GET /` every 5 minutes (`https://codex-backend-1gok.onrender.com/`).
- **However, `GET /` never touched PostgreSQL**: In `codex-backend/server.py`, the root endpoint returned purely in-memory static JSON:
  ```python
  @app.get("/")
  async def root():
      return {"status": "ok", "app": "CodexEngine V4", "version": "4.0"}
  ```
- Because zero SQL queries ran against Supabase for >7 days, Supabase flagged the project as idle despite continuous Render HTTP traffic.

### 💡 Proposal & Solution
1. **v4 (`main`)**: Update `GET /` and `GET /health` in `server.py` to execute a fast `SELECT 1;` query using SQLAlchemy `engine.connect()`:
   ```python
   @app.get("/")
   @app.get("/health")
   async def root():
       db_status = "ok"
       try:
           with engine.connect() as conn:
               conn.execute(text("SELECT 1;"))
       except Exception as e:
           logger.warning(f"Root DB ping failed: {e}")
           db_status = "error"
       return {"status": "ok", "app": "CodexEngine", "version": "4.0", "db": db_status}
   ```
2. **v5 (`agentic`)**: Implement the equivalent async query (`async with async_engine.connect() as conn: await conn.execute(text("SELECT 1;"))`).
3. **Outcome**: Every 5-minute UptimeRobot ping will automatically generate active database traffic, keeping both Render and Supabase 100% active 24/7 without extra costs.

---

## 2. Issue: Direct File Lookup Failure in RAG ("what's in my tasks.txt?")

### 🔴 The Problem
When a user uploads a document like `tasks.txt` and directly asks *"whats in my tasks.txt file?"*, the v4 engine fails to retrieve the file and falls back to hallucinated apologies (`[Source: Internal AI Knowledge] - No relevant documents found in the database. I don't have direct access to your local files...`).

### 🔍 Root Cause
1. **Routing is NOT the failure**: The LangGraph router correctly categorized the prompt as `Intent: retrieval_required` (Confidence: 90%).
2. **Database Storage is NOT the failure**: The file is properly parsed and stored in Supabase `prose_chunks`.
3. **Retrieval Mechanism Limitation in v4**:
   - **Vector Search** (`_vector_search` in `src/nodes/retriever.py`): Performs cosine similarity between the query embedding ("whats in my tasks.txt file?") and chunk *content*. If `tasks.txt` contains to-do items or lists without repeating the exact words "tasks.txt", cosine similarity is near zero.
   - **BM25 Search** (`_bm25_search` in `src/repositories/utils.py`): Indexes **only** the chunk text body (`_bm25_corpus`), completely ignoring metadata (where the filename `source: "tasks.txt"` is stored).
   - Neither search path filters by filename in `metadata->>'source'`.

### 💡 Proposal & Solution
- **For v4 (`main`)**:
  - Update `get_bm25_index()` in `src/repositories/utils.py` to prepend metadata/filename into the indexed text (e.g. `_bm25_corpus.append(f"Document File: {meta.get('source', '')}\n{content}")`).
  - Add query-regex parsing in `retriever.py` to extract filenames and apply a SQL metadata filter (`metadata->>'source' ILIKE :filename`).
- **For v5 (`agentic`)**:
  - v5 inherently solves this by providing explicit tool-calling primitives: `list_documents(pattern="tasks.txt")` and `read_document(path="tasks.txt")`, allowing the LLM to inspect files by path rather than relying purely on semantic vector matches.

---

## 3. Issue: Hardcoded Actor LLM Model in v4

### 🔴 The Problem
In `codex-backend/src/nodes/actor.py` (Line 7), the actor LLM is hardcoded:
```python
llm = get_chat_model(model="llama-3.3-70b-versatile", temperature=0.3, max_retries=3)
```

### 🔍 Root Cause & Impact
- All other pipeline nodes (`router.py`, `condenser.py`, `evaluator.py`, `rewriter.py`) call `get_chat_model(temperature=...)` without passing `model`, thereby dynamically inheriting `GROQ_MODEL_NAME` from `.env` (`qwen/qwen3.6-27b` or `llama-3.1-8b-instant`).
- Because `actor.py` hardcodes `llama-3.3-70b-versatile`, any changes to `.env` are ignored for the final generation step.
- `llama-3.3-70b` has lower rate limits on Groq free tier, leading to 429 errors during heavy multi-turn tests.

### 💡 Proposal & Solution
- In `src/nodes/actor.py`, change line 7 to:
  ```python
  llm = get_chat_model(temperature=0.3, max_retries=3)
  ```
- This allows all nodes to uniformly respect `GROQ_MODEL_NAME`.

---

## 4. Issue: LLM Provider Diversity & Fallbacks (Groq vs OpenRouter vs Gemini)

### 🔍 Current Comparison
- **v4 (`main`)**: Hardcoded to `langchain_groq.ChatGroq`. If Groq is down or rate-limited, the entire pipeline halts (only embeddings have a Gemini fallback).
- **v5 (`agentic`)**: Features a modular provider-agnostic factory (`src/llm/providers.py`) supporting:
  - **Groq** (`qwen/qwen3.6-27b`, `llama-3.1-8b-instant`, `llama-3.3-70b-versatile`)
  - **OpenRouter** (`meta-llama/llama-3.3-70b-instruct`, `gpt-4o-mini`, `openrouter/free`)
  - **Google Gemini** (`gemini-2.0-flash`, `gemini-1.5-flash` via OpenAI-compatible endpoint)
  - **Together AI** (`Qwen/Qwen2.5-70B-Instruct-Turbo`)

### 💡 Proposal & Solution
- **For v4 (`main`)**: Port the lightweight provider layer or add fallback logic inside `src/llm.py` so that if Groq returns a persistent 429/500, it automatically redirects the call to OpenRouter or Gemini.
- **For Groq Model Selection**: Set `GROQ_MODEL_NAME=qwen/qwen3.6-27b` (for higher reasoning and reliable tool calling) or `llama-3.1-8b-instant` (for maximum throughput and RPM limits).

---

## 5. Summary Matrix: Branch Action Items

| Topic | v4 (`main` Branch) Action Items | v5 (`agentic` Branch) Action Items |
| :--- | :--- | :--- |
| **Keep-Alive** | Add `SELECT 1` in `GET /` & `GET /health` in `server.py` | Add `SELECT 1` async in `GET /` in `server.py` |
| **Model Config** | Remove hardcoded `model="llama-3.3-70b"` in `actor.py` | Already provider-agnostic (`src/llm/providers.py`) |
| **File Retrieval** | Enhance BM25 to index metadata + add filename SQL filter | Test `read_document` & `list_documents` tools in Dogfooding |
| **Multi-Provider** | Consider porting OpenRouter fallback from v5 | Supported out-of-the-box (Groq, OpenRouter, Gemini, Together) |
| **CI/CD Cleanup** | `keep_alive.yml` removed; rely on UptimeRobot | `keep_alive.yml` removed; rely on UptimeRobot |

---

## 6. Next Steps & Execution Roadmap

1. **When ready to apply fixes**:
   - Apply `SELECT 1` healthcheck and `actor.py` dynamic model inheritance to `main`.
   - Verify Render deployment logs and check Supabase dashboard to ensure project is unpaused.
2. **When resuming v5 Dogfooding**:
   - Launch backend and frontend servers locally or deploy `agentic`.
   - Run **Day 1: Project Isolation Validation** (`project_id` scoping).
   - Execute Days 2–7 of the dogfooding protocol.
3. **v5.1 – v5.3 Architecture Roadmap**:
   - **v5.1**: Firecrawl deep web & documentation crawling with `MarkdownHeaderTextSplitter` (`#`, `##`, `###`).
   - **v5.2**: Composio tool integration (GitHub, Notion, Slack, Jira) directly in agent loop without MCP daemon overhead.
   - **v5.3**: Persistent agent memory conventions (`memory/`, `decisions/`, `workspace-state/session.json`).
