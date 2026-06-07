# CodexEngine V3.0 - Codebase Analysis

This document provides a comprehensive review of the `CodexEngine` repository as it stands right now. It covers architectural issues, operational bugs, bottlenecks, and missing features based on the stated roadmap and implicit requirements.

## 🚨 1. What's Wrong: Bugs & Bottlenecks

### A. Broken Test Suite (`tests/`)
The current test files (`test_golden.py` and `test_rigorous.py`) are severely broken because they target the legacy V2 architecture:
- **Missing Module:** They attempt to import `app` from `src.graph` (`from src.graph import app`), which no longer exists. The graph compilation has been moved into `server.py` (`create_graph`).
- **State Schema Mismatch:** The tests construct the initial state using `AgentState(query=...)`, but the V3 state requires `user_query` and `search_query`.
- **Output Key Mismatch:** The tests attempt to read `final_state["answer"]`, but the V3 Actor node outputs the final text to the `response` key.

### B. Synchronous Blocking in Async FastAPI
The `server.py` utilizes asynchronous FastAPI endpoints and LangGraph's async streaming (`astream_events`). However, **every node in `src/nodes/` is synchronous**.
- `llm.invoke()` is used across `router.py`, `evaluator.py`, `rewriter.py`, `actor.py`, and `condenser.py`.
- `SQLAlchemy` uses a synchronous `create_engine` with blocking `.execute()` calls in `retriever.py`.
- **Impact:** Calling synchronous LLM APIs and blocking DB queries within an async event loop will completely choke the FastAPI server under load. These need to be converted to `.ainvoke()` and asynchronous database drivers (like `asyncpg`).

### C. Hardcoded Frontend Values (`codex-ui/app/page.tsx`)
- The `thread_id` is hardcoded as `"linear_ui_test"` in the fetch request. This means every user and every "New Chat" session shares the exact same stateful memory.
- The UI handles SSE streams natively using `TextDecoder`. If a JSON payload from the backend is split across two chunks (which is common in streaming), `JSON.parse()` will throw an error and crash the chat feed.

### D. Missing Local Directories
The `data/raw/` directory required by `scripts/ingestion.py` does not exist in the repository. Running the ingestion script right now will fail.

---

## 🚧 2. What's Lacking: Missing Features

### A. V3.5 Roadmap Features (Not Yet Implemented)
The `README.md` outlines a "Roadmap to V3.5", but none of the code for these features is present:
- **Autonomous Web Search Node:** There is no integration with Tavily, DuckDuckGo, or any live internet search fallback when local context scores 0.0.
- **Local Cross-Encoder Re-ranking:** The `retriever.py` pulls the top 5 chunks from `pgvector` via cosine similarity, but there is no secondary local re-ranking layer (e.g., `ms-marco-MiniLM`) applied before passing the context to the LLM.
- **Document Upload API & UI:** The Next.js frontend has a "Manage Documents" button, but it is purely aesthetic. There is no `/upload` endpoint in `server.py` to ingest new PDFs via the UI.
- **CI/CD Benchmarking:** There are no GitHub Actions workflows (`.github/workflows/eval.yml`) set up for automated evaluation.

### B. Implicit Gaps & Best Practices
- **Lack of Structured Logging:** The backend heavily relies on `print()` statements for debugging. An enterprise RAG engine should use Python's `logging` module or a library like `loguru` to capture these events cleanly.
- **Environment Management:** There's no `.env.example` file to show developers what keys are needed (e.g., `GROQ_API_KEY`, `DB_URL`).
- **Dockerization:** Setting up PostgreSQL with `pgvector` locally can be painful. A `docker-compose.yml` file spinning up a `pgvector` database container alongside the FastAPI server would vastly improve developer experience.
- **Frontend Code Quality:** The Next.js app lacks global state management for chats (e.g., Zustand or React Context) and does not utilize proper Next.js API routes, calling the backend directly from the client.

---

## 🎯 3. Actionable Next Steps (Recommendations)

1. **Refactor to pure Async:** Update all LangChain Groq calls in `src/nodes/` to use `ainvoke` and upgrade the database connection in `retriever.py` to use an async engine (like the `AsyncConnectionPool` already imported in `server.py`).
2. **Fix the Evals Suite:** Update the scripts in `tests/` to properly initialize the state dictionary and import the graph via `server.create_graph`.
3. **Dynamic Memory in UI:** Generate a UUID on the frontend when "New Chat" is clicked, and pass it as the `thread_id` to ensure isolated conversation memory.
4. **Implement Missing Nodes:** Add a fallback web search tool in the LangGraph conditional edges and insert a re-ranking function in `retriever.py`.
5. **Add Docker-Compose:** Provide a unified setup environment for the database and engine.
