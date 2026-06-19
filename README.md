# CodexEngine V4.0 — Knowledge Operating System

Stateful, multi-agent RAG system with LangGraph orchestration, pgvector, Supabase auth/storage, and a Next.js glassmorphic UI.

## Architecture

```mermaid
flowchart TD
    User([User / Browser])

    subgraph Frontend [codex-frontend — Next.js 16]
        AuthUI[Auth UI]
        ChatUI[Chat UI / SSE]
        DocMgr[Document Manager]
        SupaSDK["@supabase/supabase-js<br>Auth JWT → Bearer"]
    end

    subgraph Supabase [Supabase]
        SA[Auth<br>sign up / sign in]
        SB[Storage<br>documents bucket]
    end

    subgraph Backend [codex-backend — FastAPI + Uvicorn]
        direction LR
        R[1. Router] --> C[2. Condenser] --> Ret[3. Retriever]
        Ret --> E[4. Evaluator]
        E -->|loop ≤3x| RW[5. Rewriter]
        RW --> Ret
        E --> A[6. Actor]
        A --> Resp[SSE Response]

        subgraph Retrieval [Hybrid Retrieval]
            VEC[Vector Search]
            BM[BM25 Keyword]
            WEB[DuckDuckGo<br>Web Fallback]
            Fuse[Fusion + Rerank]
        end
    end

    subgraph DB [PostgreSQL + pgvector]
        Threads[threads]
        Chunks[prose_chunks<br>384-dim vectors]
    end

    subgraph External [External APIs]
        Groq[Groq<br>LLM — llama-3.1]
        Gemini[Google Gemini<br>embeddings — production]
        FastEmbed[fastembed ONNX<br>embeddings — local/CI]
    end

    User --> Frontend
    AuthUI --> SA
    SA -.->|JWT session| SupaSDK
    SupaSDK --> Backend
    ChatUI <-->|SSE stream| Backend
    DocMgr <-->|upload / list / delete| Backend

    Backend --> SB
    Backend --> DB
    Ret --> VEC
    Ret --> BM
    Ret --> WEB
    VEC & BM & WEB --> Fuse
    Fuse --> Ret

    VEC ---> FastEmbed
    VEC -.->|fallback| Gemini
    Backend ---> Groq
```

### Running Modes

The system auto-detects its environment and switches between two modes:

| Feature | Local / CI (≥1.5GB RAM) | Render Production (512MB) |
|---|---|---|
| Embeddings | fastembed ONNX (`bge-small-en-v1.5`) | Google Gemini API |
| Reranker | CrossEncoder (`ms-marco-MiniLM-L-6-v2`) | Score-based sort fallback |
| Detection | `MemTotal > 1.5GB` → local mode | `MemTotal < 1.5GB` → Gemini-only |

Both produce **384-dimensional vectors** compatible with the `vector(384)` schema.

## Quick Start

### Prerequisites

- Python 3.12+, Node.js 20+
- PostgreSQL with pgvector (Docker: `docker compose up -d db` or native install)
- [Groq API key](https://console.groq.com/keys) (LLM)
- [Google API key](https://aistudio.google.com/app/apikey) (production embeddings — free tier)
- [Supabase project](https://supabase.com) (free tier) — auth + storage + cloud DB

### Backend

```bash
cd codex-backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd codex-frontend
npm install && npm run dev
# Set NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY,
# NEXT_PUBLIC_API_URL in .env.local
```

## Testing

```bash
cd codex-backend
source .venv/bin/activate
python tests/test_golden.py       # Single golden query
python tests/test_rigorous.py     # Full sweep
python eval/ragas_eval.py         # RAGAS metrics
```

## Learn More

- [Deployment guide](docs/deployment.md) — Render, Vercel, Supabase setup
- [API reference](docs/api.md) — endpoint table with request/response examples
