# CodexEngine — status handoff (this checkout)

| Field | Value |
|-------|--------|
| **As of** | 2026-07-19 |
| **Remote** | `anmolsharma152/CodexEngine` |
| **This folder** | Often cloned as `CodexEngine Demo V2.5` locally — **same remote** as `~/Projects/CodexEngine` |
| **Stable branch** | `main` — v4 document intelligence (ingest, hybrid retrieval, citations, FastAPI + Next.js) |
| **Experimental** | `agentic` — v5 workspace agent (artifacts, flexible tool loop) |

---

## Prefer which tree?

| Goal | Use |
|------|-----|
| Production-shaped doc Q&A (v4) | `main` (this branch when on main) |
| Workspace agent experiments (v5) | `agentic` in `~/Projects/CodexEngine` — see that tree’s `docs/STATUS.md` |

Do not confuse legacy V2.5 LangGraph critic-loop experiments (older notes) with current `main`/`agentic` layout (`codex-backend` / `codex-frontend`).

---

## Resume

1. Confirm branch: `git branch -vv`  
2. Read root README + [setup.md](./setup.md)  
3. For v5 work, switch to `agentic` (or the other local clone) and its AGENTS.md  

Never commit secrets.
