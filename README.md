# CodexEngine

A self-hosted document intelligence platform that lets you upload documents, ask questions, and get answers backed by source citations.

The project currently has two tracks:

- v4: a stable retrieval-first research engine
- v5: an experimental workspace agent that creates and reuses persistent artifacts

## Repository Structure

### Stable Release (v4)

The `main` branch contains the stable document intelligence platform:

- PDF and document ingestion
- Hybrid retrieval (vector search + BM25)
- Source citations
- FastAPI backend
- Next.js frontend
- PostgreSQL + pgvector
- Self-hosted deployment

### Experimental Development (v5)

Active development is happening on the `agentic` branch.

The current research direction explores whether persistent artifacts can make AI assistants more useful than chat alone. Instead of relying entirely on conversation history, the agent creates, stores, and reuses workspace artifacts across sessions.

Highlights:

- Custom agent loop (no LangGraph)
- Provider-agnostic LLM layer
- Workspace artifacts
- Persistent context experiments
- Tool-driven architecture

➡️ Experimental branch:
<https://github.com/anmolsharma152/CodexEngine/tree/agentic>

## Why This Project Exists

Most document assistants answer a question and immediately forget the work they just performed.

CodexEngine started as a retrieval-augmented research system and is evolving into an experiment around persistent AI workspaces, where analysis, reports, and findings can become reusable knowledge objects.

CodexEngine began as a retrieval-first research engine and is now being used to explore persistent AI workspaces.

## Branches

| Branch    | Status       | Purpose                                     |
| --------- | ------------ | ------------------------------------------- |
| `main`    | Stable       | Production-ready document intelligence platform (v4) |
| `agentic` | Experimental | Workspace-agent research and v5 development |

## Quick Start

```bash
git clone https://github.com/anmolsharma152/CodexEngine.git
cd CodexEngine

# Backend
cd codex-backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn server:app --reload --host 127.0.0.1 --port 8000

# Frontend (new terminal)
cd codex-frontend
npm install && npm run dev
```

Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL` in `codex-frontend/.env.local`. Open `http://localhost:3000` — register, upload a PDF, and start asking questions.

## How It Works

When you ask a question, CodexEngine:

1. Decides if it needs to search your documents or can answer directly
2. Searches your indexed content using vector similarity + keyword search + optional web fallback
3. Scores and reranks the results
4. Generates an answer with source citations (`[p. X]`, `[r. X]`, `[doc]`, `[web]`)

All of this runs through the v4 retrieval pipeline, which currently uses LangGraph-based orchestration and self-evaluation loops (up to 3 retries if the initial answer is weak).

The experimental `agentic` branch replaces this architecture with a custom agent loop.

### Running Modes

| Feature    | Local / CI                              | Production (Render 512MB)  |
| ---------- | --------------------------------------- | -------------------------- |
| Embeddings | fastembed ONNX (`bge-small-en-v1.5`)    | Google Gemini API          |
| Reranker   | CrossEncoder (`ms-marco-MiniLM-L-6-v2`) | Score-based sort           |
| Detection  | `MemTotal > 1.5GB` or no `RENDER` env   | `RENDER=true` or `< 1.5GB` |

Both modes produce 384-dimensional vectors.

## Architecture

```mermaid
flowchart TD
    User([User / Browser])

    subgraph Frontend [codex-frontend — Next.js 15]
        AuthUI[Auth UI]
        ChatUI[Chat UI / SSE]
        DocMgr[Document Manager]
        SupaSDK["@supabase/supabase-js<br>Auth JWT → Bearer"]
    end

    subgraph Supabase [Supabase]
        SA[Auth<br>sign up / sign in]
        SB[Storage<br>documents bucket]
    end

    subgraph Backend [codex-backend — FastAPI]
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
        Gemini[Google Gemini<br>embeddings]
        FastEmbed[fastembed ONNX<br>embeddings]
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

## Technical Highlights

- FastAPI backend
- Next.js frontend
- PostgreSQL + pgvector
- Hybrid retrieval (vector + BM25)
- Server-sent events (SSE) streaming
- Supabase authentication and storage
- Provider-agnostic LLM architecture
- Workspace-agent experimentation (v5)
