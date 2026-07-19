# CodexEngine — setup

| Field | Value |
|-------|--------|
| **As of** | 2026-07-19 |
| **Preferred branch for v5** | `agentic` |

Status: [STATUS.md](./STATUS.md). Deploy: [deployment.md](./deployment.md). Root [README.md](../README.md).

---

## Components

| Dir | Role |
|-----|------|
| `codex-backend/` | FastAPI, agent loop, tools, DB |
| `codex-frontend/` | Next.js UI + Supabase auth |
| `docker-compose.yml` | Local stack (when used) |
| `render.yaml` | Hosted deploy sketch |

---

## Typical env groups

| Group | Examples |
|-------|----------|
| Supabase | URL, anon key, service role (server only) |
| Database | `DATABASE_URL` / asyncpg URL |
| LLM | Groq / OpenAI / Together API keys |
| Embeddings | Provider key used for vector search |

Never commit `.env` files. Prefer `.env.example` templates in backend/frontend.

---

## Quick start (high level)

```bash
cd ~/Projects/CodexEngine
git checkout agentic   # for v5
# fill env files per README / deployment.md
docker compose up
# OR:
# backend: uvicorn ... from codex-backend
# frontend: npm run dev from codex-frontend
```

Exact commands change with branch — always verify README for that branch.

---

## Ops notes

- Project-scoped artifacts: `project_id` injected server-side  
- SSE endpoint for chat streaming  
- Tool invocations may log to `tool_invocations`  
