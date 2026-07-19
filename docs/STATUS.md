# CodexEngine — status handoff

| Field | Value |
|-------|--------|
| **As of** | 2026-07-19 |
| **Active branch** | `agentic` (v5 experimental) |
| **Stable historical** | `main` (v4 LangGraph research engine) |
| **Product** | Workspace agent — document RAG + persistent artifacts + flexible tool loop |
| **Stability** | Experimental — APIs/schemas may change |

Agent architecture detail: [../AGENTS.md](../AGENTS.md). Deployment notes: [deployment.md](./deployment.md). API: [api.md](./api.md).

---

## What ships on `agentic` (v5)

| Feature | Status |
|---------|--------|
| Custom while-true agent loop | ✅ LLM decides tools vs respond |
| Provider-agnostic LLM layer | ✅ Groq / OpenAI / Together / … |
| Tools | ✅ search_documents, search_web, read/write/list_documents |
| Workspace artifacts + project isolation | ✅ |
| SSE streaming chat | ✅ |
| Next.js frontend + Supabase auth | ✅ (codex-frontend) |
| Postgres + pgvector | ✅ |

v4 on `main` remains the hardcoded LangGraph DAG path for comparison.

---

## Architecture snapshot

```text
Next.js (codex-frontend)  →  FastAPI (codex-backend)  →  agent loop + tools
         Supabase JWT              Postgres / pgvector / artifacts
```

---

## Known gaps

- [ ] Not production-hardened (rate limits, multi-tenant ops)  
- [ ] Schema/API churn risk on `agentic`  
- [ ] Align product strategy doc ([product-strategy-agentic.md](./product-strategy-agentic.md) if present) with shipped tools  

### Portfolio adjacency
- IdeaForge may **reuse patterns** (workspace memory) — do not merge repos.  
- Ozyman / Disha / Scholar-Loop are separate products.

---

## Local dev checklist

```bash
cd ~/Projects/CodexEngine
# See README + docs/deployment.md for compose / env
docker compose up   # if using full stack
# or run codex-backend + codex-frontend separately per README
```

---

## Resume protocol

1. Confirm branch (`agentic` vs `main`).  
2. Read [../AGENTS.md](../AGENTS.md) for v5 loop semantics.  
3. Never commit secrets; respect project isolation on artifacts.
