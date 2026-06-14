# CodexEngine V4.0 - Knowledge Operating System

Stateful, multi-agent RAG system with LangGraph orchestration, pgvector, and a Next.js glassmorphic UI.

## Architecture

```
CodexEngine/
├── codex-backend/
│   ├── server.py              # FastAPI app (SSE streaming, auth, CRUD)
│   ├── src/
│   │   ├── state.py           # TypedDict AgentState schema
│   │   ├── repositories/
│   │   │   └── utils.py       # FastEmbed + BM25 + reranker setup
│   │   └── nodes/
│   │       ├── router.py      # Intent classifier (3-lane)
│   │       ├── retriever.py   # Hybrid: vector + BM25 + cross-encoder rerank
│   │       ├── evaluator.py   # Critic: structured JSON evaluator
│   │       ├── rewriter.py    # Search query optimizer
│   │       ├── condenser.py   # Memory/history resolution
│   │       ├── actor.py       # Response synthesis with provenance
│   │       └── nodes.py       # Export hub
│   ├── scripts/
│   │   └── ingestion.py       # PDF/CSV/TXT ingestion
│   ├── tests/
│   │   ├── test_golden.py     # Single golden query
│   │   └── test_rigorous.py   # Full sweep of 5 queries
│   ├── eval/
│   │   ├── ragas_eval.py      # Groq-based RAGAS metrics
│   │   └── golden_queries.json
│   ├── data/raw/              # PDF knowledge base
│   ├── Dockerfile
│   └── requirements.txt
├── codex-frontend/            # Next.js frontend
├── docker-compose.yml
└── .github/workflows/eval.yml # CI pipeline
```

## Quick Start

```bash
# 1. Backend
cd codex-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env           # edit with your GROQ_API_KEY

# 2. Database (from repo root)
docker compose up -d           # runs pgvector on 5432

# 3. Ingest files
cp your.pdf data/raw/
python scripts/ingestion.py

# 4. Start server
uvicorn server:app --reload --host 127.0.0.1 --port 8000

# 5. Frontend (separate terminal)
cd codex-frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Create account |
| POST | `/login` | No | Get JWT token |
| GET | `/user/me` | Yes | Current user info |
| GET | `/threads` | Yes | List threads |
| POST | `/threads` | Yes | Create/update thread |
| DELETE | `/threads/{id}` | Yes | Delete thread |
| POST | `/chat/stream` | Yes | SSE streaming chat |
| GET | `/chat/{id}/history` | Yes | Message history |
| POST | `/upload` | Yes | Ingest document |
| POST | `/upload/temporal` | Yes | Session-scoped upload |
| GET | `/documents` | Yes | List documents |
| DELETE | `/documents/{filename}` | Yes | Delete document |

## Testing

```bash
cd codex-backend
source venv/bin/activate
python tests/test_golden.py       # Single query
python tests/test_rigorous.py     # Full sweep
python eval/ragas_eval.py         # RAGAS metrics (Groq-based)
```
