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

| Phase | Tools |
|---|---|
| **v5.0 Core** | `vector_search`, `keyword_search`, `web_search`, `read_document`, `list_documents` |
| **v5.1 Write** | `write_document`, `edit_document`, `create_file` |
| **v5.2 Comms** | `compose_email`, `summarize`, `compare_documents` |
| **Future** | MCP adapter (discover external tools dynamically) |

## Key Design Decisions

| Decision | Rationale | Source |
|---|---|---|
| **Custom loop, not LangGraph** | ~150 lines, no framework lock-in, direct SSE control | Pi, opencode, Codex CLI |
| **@tool decorators with typed schemas** | Auto-generate tool definitions from function signatures | opencode tool registry |
| **SSE streaming with tool events** | Emit tool start/result tokens so UI shows progress | Current SSE pattern |
| **Proactive summarization** | 3-step (summary → questions → answers) before context limit | Terminus-2 |
| **Multi-tool, not mono-tool** | Document Q&A needs discrete semantic tools, not terminal | Domain fit |
| **Flexible orchestration** | Support both single-loop and subagent patterns; not hardcoded | opencode, Codex CLI, Pi |
| **Python-only for v5.0** | Rust/TS for perf-critical subsystems later | Phased expansion |

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

Subagent spawning is optional — start with single-loop, add subagents when parallel exploration is needed.

## Implementation Order

1. Core agent loop — `agent_loop.py` with LLM → tool → loop pattern
2. Migrate existing RAG nodes as `@tool` functions
3. SSE streaming — emit tool events to frontend
4. Context management — proactive summarization
5. Write tools — `write_document`, `edit_document`
6. Subagent spawning (optional) — for parallel subtasks
7. MCP adapter — dynamic tool discovery
8. Language expansion — Rust/TS for perf-critical subsystems

## What Stays from v4.0

- Supabase auth + storage + DB
- FastAPI server + endpoints
- SSE streaming pattern
- Frontend Next.js app
- Dual-mode embeddings (fastembed/Gemini)

## What Gets Replaced

- LangGraph `StateGraph` → custom agent loop (flexible: single-loop or subagent)
- Fixed pipeline nodes → dynamic tool selection via `@tool` decorators
- LangGraph checkpointing → custom message persistence via `chat_messages` table

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
