# Deployment

## Branch Strategy

| Branch | Purpose | Deployed |
|---|---|---|
| `main` | v4.0 stable — LangGraph pipeline | ✅ Render + Vercel |
| `agentic` | v5.0 rewrite — custom agent loop with @tool registry | ❌ Under development |

## Environment Variables

| Service | Config File | Variables |
|---|---|---|
| **Render** (backend) | `render.yaml` | `DB_URL`, `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `GOOGLE_API_KEY`, `ALLOWED_ORIGINS` |
| **Vercel** (frontend) | Project Settings → Environment Variables | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL` |

## Steps

### 1. Supabase Project

1. Create a free project at [supabase.com](https://supabase.com)
2. **Auth**: Settings → Auth → Email → toggle **Confirm email OFF**
3. **SQL**: Run `codex-backend/supabase/seed.sql` in Supabase SQL Editor to create tables, storage bucket, and RLS policies

### 2. Backend (Render)

1. Connect your GitHub repo to Render via **Blueprint** (use `main` branch for v4, `agentic` for v5)
2. Render reads `render.yaml` — set the env vars in the dashboard or blueprint
3. Deploy — the service auto-starts at `https://<your-app>.onrender.com`
4. **Verify**: `curl https://<your-app>.onrender.com/` → `{"status":"ok","app":"CodexEngine V4","version":"4.0"}`

### 3. Frontend (Vercel)

1. Import the repo, set root directory to `codex-frontend`
2. Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL` in Vercel project settings
3. Deploy — the UI is live at `https://<your-app>.vercel.app`

### 4. Post-Deploy

- Update `ALLOWED_ORIGINS` on Render to include your Vercel URL
- Run `codex-backend/supabase/seed.sql` on the cloud DB if not done already

## CI/CD

GitHub Actions runs on every push to `main`:

- Spins up a local `pgvector` container
- Installs dependencies (includes fastembed for local/CI mode)
- Seeds the database schema
- Runs golden tests, rigorous sweep, and RAGAS eval

**Required secrets** (repo → Settings → Secrets and variables → Actions → Repository secrets):

| Secret | Purpose |
|---|---|
| `GROQ_API_KEY` | LLM inference |
| `GOOGLE_API_KEY` | Embeddings (used as fallback in CI) |
