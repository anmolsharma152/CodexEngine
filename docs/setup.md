# CodexEngine — setup (shared remote)

Status: [STATUS.md](./STATUS.md). Prefer root README Quick Start.

```bash
# Either local path is fine if remote is CodexEngine:
cd ~/Projects/CodexEngine
# or: cd "~/Projects/CodexEngine Demo V2.5"

git checkout main      # stable v4
# git checkout agentic # experimental v5

# Backend
cd codex-backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn server:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd ../codex-frontend && npm install && npm run dev
```

Also see [deployment.md](./deployment.md) when present.
