# Deployment

## Branch Strategy

| Branch | Purpose | Deployed | Merge Rule |
|---|---|---|---|---|
| `main` | v4 stable — LangGraph pipeline | ✅ Render + Vercel | **Protected.** PR from `agentic` requires review. |
| `agentic` | v5 experimental — custom agent loop with @tool registry | ❌ Under development | Merges to `main` when stable. |

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

## Production Keep-Alive & Monitoring Strategy

To prevent **Render free tier spin-down** (15-minute idle timeout) and **Supabase auto-pause** (7-day inactivity pause), CodexEngine uses a **Hybrid Keep-Alive Pattern**:

### 🥇 Primary Solution: UptimeRobot (Real-Time Monitor)
- **Setup**: Create a free HTTP monitor at [UptimeRobot.com](https://uptimerobot.com/) targeting `https://<your-backend>.onrender.com/` (or `/health`) every **5 minutes**.
- **Why Primary**: Guarantees exact 5-minute precision without runner queue delays, keeps Render 100% warm 24/7, and instantly notifies via Email/Slack if the service crashes.

### 🥈 Secondary Backup: GitHub Actions Workflow (`.github/workflows/keep_alive.yml`)
- **Setup**: Automatically enabled via `.github/workflows/keep_alive.yml` in the repository running every 14 minutes (`cron: '*/14 * * * *'`).
- **Function**: Sends HTTP requests to both Render backend (`secrets.RENDER_BACKEND_URL`) and Supabase REST API (`secrets.SUPABASE_URL`) as an in-repo automated backup.

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
