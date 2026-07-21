# CodexEngine v5 — Experimental Workspace Agent

> **Status:** Experimental — Active Development — Not Production-Ready



CodexEngine v5 is an experimental evolution of the v4 research engine.
The agent doesn't just answer questions — it can create persistent
workspace artifacts and read them later, allowing work from one session
to be reused in future conversations.

---

## Status

- **Branch:** `agentic`
- **Stage:** Active research and development
- **Stability:** Subject to rebasing, API changes, and schema migrations
- **Not production-ready** - APIs, schemas, and behavior may change without notice.

---

## What Changed From v4

| Feature               | v4 (`main`)                          | v5 (`agentic`)                                      |
| --------------------- | ------------------------------------ | --------------------------------------------------- |
| Agent framework       | LangGraph StateGraph (hardcoded DAG) | Custom while-true loop (LLM decides)                |
| Tool model            | 6 fixed pipeline nodes               | 5 `@tool`-decorated functions                       |
| LLM providers         | Groq only                            | Groq, OpenAI, Together, Gemini                      |
| Tool definitions      | Generated manually                   | Auto-generated from type hints + docstrings         |
| Workspace Persistence | None                                 | Workspace artifacts                                 |
| Artifact tools        | None                                 | `read_document`, `write_document`, `list_documents` |
| Project isolation     | None                                 | `project_id` scoping for all artifacts              |
| Instrumentation       | Limited                              | tool_invocations logging table                      |
| SSE events            | Full pipeline state                  | Status, tool_call, tool_result, token, done, error  |
| Message storage       | LangGraph checkpointer               | `chat_messages` table (manual persistence)          |

---

## Architecture

The agent loop is intentionally small and framework-light.
The LLM receives tool definitions and decides per-turn whether to call a
tool or respond directly.

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

### Tools

| Tool               | Purpose                                               |
| ------------------ | ----------------------------------------------------- |
| `search_documents` | Hybrid vector + BM25 search across uploaded documents |
| `search_web`       | DuckDuckGo fallback for external information          |
| `read_document`    | Read a workspace artifact by path                     |
| `write_document`   | Create or overwrite a workspace artifact              |
| `list_documents`   | List artifacts, optionally filtered by path pattern   |

### Project Isolation

Every artifact is scoped to a `project_id`. The agent loop injects the
active project ID into all workspace tool calls automatically — the LLM
does not need to populate it. This ensures:

- Artifacts in project A are invisible from project B
- `list_documents` returns only artifacts for the active project
- Cross-project leaks are prevented at the query level

### How It Works

When you ask a question, CodexEngine runs a flexible agent loop — the
LLM decides dynamically which tools to call and in what order:

1. **Search documents** — Hybrid vector + BM25 search across your indexed
   documents
2. **Search web** — DuckDuckGo fallback for external information
3. **Read/write artifacts** — Create and consume persistent workspace
   documents
4. **Generate** — Produces a final answer with source citations
   (`[p. X]`, `[r. X]`, `[doc]`, `[web]`)

For a detailed architecture diagram and agent design notes, see AGENTS.md.

---

## Research Questions

The workspace experiment exists to gather evidence on:

1. **Artifact usefulness** — Do persistent artifacts improve output quality
   compared to chat-only responses?

2. **Artifact reuse** — Will the agent read artifacts it wrote previously,
   or does it start from scratch every session?

3. **Project isolation** — When artifacts are scoped to projects, does the
   agent respect project boundaries?

4. **Artifact vs. search preference** — When answering a question that could
   be answered from either an artifact or a fresh retrieval, which does the
   agent choose?

5. **Cross-session continuity** — Can the agent carry context across sessions
   by reading its own artifacts?

---

## Dogfooding Status

A 7-day evaluation plan is in progress. The plan covers:

- **Day 1:** Project isolation baseline (create artifacts in two projects,
  verify no leaks)
- **Day 2:** Artifact production + same-session reuse (write, then read back)
- **Day 3:** Artifact vs. search preference (cold question an artifact can
  answer — the most important test)
- **Day 4:** Overwrite awareness + path conventions
- **Day 5:** Cross-session reuse (24-hour gap)
- **Day 6:** Project switching + cross-project isolation
- **Day 7:** Retrospective + evidence compilation

Each day includes exact prompts, expected tool calls, failure signals,
and SQL queries for evidence collection.

See the full plan at [docs/7-day-dogfooding-plan.md](docs/7-day-dogfooding-plan.md).

---

## Quick Start

```bash
git clone https://github.com/anmolsharma152/CodexEngine.git
cd CodexEngine
git checkout agentic

# Backend
cd codex-backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn server:app --reload --host 127.0.0.1 --port 8000

# Frontend (new terminal)
cd codex-frontend
npm install && npm run dev
```

Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`,
`NEXT_PUBLIC_API_URL` in `codex-frontend/.env.local`.

Open `http://localhost:3000` — register, upload a PDF, and start asking
questions.

### Running Modes

| Feature    | Local / CI                              | Production (Render 512MB)  |
| ---------- | --------------------------------------- | -------------------------- |
| Embeddings | fastembed ONNX (`bge-small-en-v1.5`)    | Google Gemini API          |
| Reranker   | CrossEncoder (`ms-marco-MiniLM-L-6-v2`) | Score-based sort           |
| Detection  | `MemTotal > 1.5GB` or no `RENDER` env   | `RENDER=true` or `< 1.5GB` |

---

## Relationship To Main

This repository has three long-lived branches:

| Branch                      | Purpose                         | Status                       |
| --------------------------- | ------------------------------- | ---------------------------- |
| `main`                      | Stable v4 research engine       | Production (Render + Vercel) |
| `agentic` **(this branch)** | Experimental v5 workspace agent | Active research              |

The root `README.md` on the `main` branch is the canonical
repository-level landing page. This document is the branch-specific
v5 README — it describes the experimental features and research goals
that differ from the stable v4 release.

---

## Learn More

- [Documentation index](docs/README.md) — complete map of all documentation
- [7-Day Dogfooding Plan](docs/7-day-dogfooding-plan.md) — day-by-day evaluation protocol
- [Workspace Experiment](codex-backend/docs/workspace-experiment.md) — hypothesis, metrics, success criteria
- [Project Isolation Validation](codex-backend/docs/project-isolation-validation.md) — `project_id` end-to-end tests
- [Future Memory Model](codex-backend/docs/future-memory-model.md) — research notes for post-MVP architecture
- [Dogfooding Checklist](codex-backend/docs/dogfooding-checklist.md) — quick-reference scorecard
- [Deployment guide](docs/deployment.md) — Render, Vercel, Supabase setup
- [API reference](docs/api.md) — endpoint table with request/response examples
- [Agent architecture](AGENTS.md) — agent loop design, tool registry, reference research
