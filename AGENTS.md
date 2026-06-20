# CodexEngine — Agentic Architecture

## Vision

Evolution from **doc Q&A bot** → **knowledge workspace agent** that can read, write, edit, synthesize, and compose — operating on documents, information, and knowledge tasks.

## Agent Loop (Replaces LangGraph Pipeline)

The core pattern is a **flexible agent loop** — not a hardcoded DAG. The LLM decides dynamically:

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
│  │ spawn subagent       │───→│ delegated task
│  └──────────────────────┘    │
└──────────────────────────────┘
```

### Two Viable Patterns (both supported)

| Pattern | When to Use | Example |
|---|---|---|
| **Single-loop tool calls** | Self-contained tasks, sequential reasoning | `vector_search` → `read_document` → respond |
| **Subagent spawning** | Parallel exploration, nested subtasks | Spawn agent to research topic A while main agent works on topic B |

The loop is **not prescribed** — the tool registry and LLM steering determine the execution path at runtime. No hardcoded LangGraph-like DAG.

## Tool Registry

### Current (v5.0 MVP)

| Tool | Description | Source |
|---|---|---|
| `analyze_intent` | Classify query as direct_casual / direct_parametric / retrieval_required | Migrated from LangGraph router |
| `vector_search` | Hybrid vector + BM25 document search with reranking | Migrated from LangGraph retriever |
| `web_search` | DuckDuckGo fallback for external info | Migrated from LangGraph retriever |
| `evaluate_retrieval` | Check if retrieved context is sufficient to answer | Migrated from LangGraph evaluator |
| `rewrite_query` | Improve search query that yielded poor results | Migrated from LangGraph rewriter |

### Planned (v5.x)

| Phase | Tools |
|---|---|
| **Doc tools** | `read_document`, `list_documents`, `keyword_search` |
| **Write tools** | `write_document`, `edit_document`, `create_file` |
| **Comms** | `compose_email`, `summarize`, `compare_documents` |
| **MCP adapter** | Discover external tools dynamically (Notion, Google Docs, Confluence) |

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Custom loop, not LangGraph** | ~170 lines, no framework lock-in, direct SSE control |
| **@tool decorators with typed schemas** | Auto-generate tool definitions from function signatures |
| **Multi-tool, not mono-tool** | Knowledge workspace needs discrete semantic tools, not terminal access |
| **Python-only for v5.0** | Rust/TS for perf-critical subsystems later |
| **Parallel tool execution** | Default concurrent execution for independent tools (pi pattern); sequential fallback for dependent tools |
| **No ATIF trajectory format** | Overkill for MVP — simple SSE JSON events suffice for frontend progress display |
| **No permission scoping** | Single-user app — every tool is available to the agent |
| **No steering/follow-up queues** | Not needed for doc Q&A; can add if conversational needs grow |

## What We Adopted (and Skipped) from References

| Reference | Adopted | Skipped |
|---|---|---|
| **opencode** | `@tool` decorator pattern, ToolRegistry singleton | No Effect-TS (overkill for Python), no permission filtering (single-user), no FiberSet (Python asyncio.gather is simpler) |
| **pi** | Two-level loop concept, parallel tool execution default, event-system via SSE | No steering queues (not needed for doc Q&A), no lifecycle hooks (add later if needed), no AgentHarness (would be one more layer of abstraction) |
| **Terminus-2** | 3-step summarization (future), subagent spawning pattern (future) | No ATIF trajectory (overkill), no mono-tool restriction, no double-completion protocol (not building a terminal agent) |
| **Codex CLI** | Sandbox-isolated tool execution (future), session-based persistence (future) | No bash execution (we're not a coding agent) |

## Implementation Status

```
✅ 1. Core agent loop — agent_loop.py with LLM → tool → loop pattern
✅ 2. Migrate existing RAG nodes as @tool functions (5 tools)
⬜ 3. Token-level SSE streaming — yield chunks, not full responses
⬜ 4. Parallel tool execution — gather independent tools concurrently
⬜ 5. Document tools — read_document, list_documents, keyword_search
⬜ 6. chat_messages table — replace LangGraph checkpointer persistence
⬜ 7. Async DB — create_async_engine → asyncpg
⬜ 8. Context management — proactive summarization (Terminus-2 3-step)
⬜ 9. Write tools — write_document, edit_document, create_file
⬜ 10. Subagent spawning — for parallel document exploration
⬜ 11. MCP adapter — Notion, Google Docs, Confluence integrations
```

## Execution Model

```
LLM Response
   │
   ├── tool_call(s) ─── execute tool ───→ append result ───→ LLM decides again
   ├── respond         ─── stream to user ───→ done
   └── subagent        ─── spawn child agent ───→ merge results ───→ LLM decides
```

- **Tool calls**: LLM requests one or more tool invocations. Results are appended to context. Loop continues.
- **Direct response**: LLM produces a final answer. Streamed to user. Session ends.
- **Subagent**: LLM delegates a subtask to a child agent (with narrowed tools/context). Child result is merged back.

## What Stays from v4.0

- Supabase auth + storage + DB
- FastAPI server + endpoints
- SSE streaming pattern
- Frontend Next.js app
- Dual-mode embeddings (fastembed/Gemini)

## What Gets Replaced

- LangGraph `StateGraph` → custom agent loop (flexible: single-loop or subagent) — **DONE**
- Fixed pipeline nodes → dynamic tool selection via `@tool` decorators — **DONE**
- LangGraph checkpointing → custom message persistence via `chat_messages` table — **TODO**

## Branch Strategy

| Branch | Purpose | Deployed |
|---|---|---|
| `main` | v4.0 stable — production | ✅ Render + Vercel |
| `release/v4.0` | Static v4.0 reference | ❌ |
| `agentic` | THIS BRANCH — v5.0 rewrite | ❌ |

## References (Research)

- opencode: https://github.com/anomalyco/opencode — tool registry, session processor
- Codex CLI: https://github.com/openai/codex — sandbox isolation, session-based
- Terminus-2/Harbor: https://www.harborframework.com/docs/agents/terminus-2 — mono-tool loop, 3-step summarization, ATIF trajectory format
- Pi: https://github.com/earendil-works/pi — layered agent toolkit (pi-ai → pi-agent-core)
