# Architecture Overview

CodexEngine is a multi-tenant document intelligence platform built on a hybrid retrieval architecture.

## System Architecture

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

    subgraph Backend [codex-backend — FastAPI]
        direction LR
        
        %% Graph Flow
        R[1. Router] -->|retrieval_required| C[2. Condenser]
        R -->|direct/meta| A[6. Actor]
        C --> Ret[3. Retriever]
        Ret --> E[4. Evaluator]
        E -->|retry_needed| RW[5. Rewriter]
        RW --> Ret
        E -->|sufficient: False| WS[Web Search Fallback]
        E -->|sufficient: True| A
        WS --> A
        A --> Resp[SSE Response]

        %% Ingestion Flow
        subgraph Ingestion [Background Ingestion]
            Q[(asyncio.Queue)]
            Worker[Worker Task]
            Q --> Worker
            Worker -->|Chunk & Embed| DB
        end
    end

    subgraph DB [PostgreSQL + pgvector]
        Threads[threads]
        Chunks[prose_chunks<br>384-dim vectors]
    end

    subgraph External [External APIs]
        Groq[Groq<br>Qwen 27B / Llama 3.1]
        Gemini[Google Gemini<br>embeddings fallback]
        FastEmbed[fastembed ONNX<br>embeddings primary]
    end

    User --> Frontend
    AuthUI --> SA
    SA -.->|JWT session| SupaSDK
    SupaSDK --> Backend
    ChatUI <-->|SSE stream| Backend
    DocMgr -->|upload to| SB
    DocMgr -->|enqueue| Q
    
    Backend --> DB
    
    Ret ---> FastEmbed
    Ret -.->|fallback| Gemini
    Backend ---> Groq
```

## Embeddings & Hybrid Fallback Architecture

CodexEngine employs a hybrid local-first embedding strategy (`src/repositories/utils.py`) to maximize local inference speed and eliminate API costs, while seamlessly falling back to Google Gemini on low-RAM server environments:

```mermaid
graph TD
    A["get_embedding_function()"] --> B{"Check System RAM / Environment"}
    B -- "RAM >= 1.5 GB (Local Machine / High-RAM CI)" --> C["FastEmbed (BAAI/bge-small-en-v1.5)"]
    C --> D["Runs locally in-process via ONNX Runtime CPU (384-dim)"]
    B -- "Low RAM / RENDER='true'" --> E["Google Gemini API (text-embedding-004)"]
    C -- "Import / Load Error" --> E
    E --> F["Cloud API Embedding Generation (384-dim)"]
```
