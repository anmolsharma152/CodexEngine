# 🏛️ CodexEngine V4.0 - Cognitive Knowledge Operating System

An enterprise-grade, stateful cognitive retrieval and multi-agent orchestration system. CodexEngine V4.0 moves beyond linear pipelines by introducing a deterministic **Actor-Critic state machine** built around LangGraph, FastAPI, PostgreSQL (`pgvector`), and a premium glassmorphic Next.js Command Center.

---

## 🚀 Architecture: The Traffic Cop & The Agentic Loop

To optimize latency and token footprint, CodexEngine routes user queries through specialized agentic nodes:

```mermaid
graph TD
    User([User Query]) --> Router{Intent Router}
    
    Router -->|direct_casual| Actor[Actor Node]
    Router -->|direct_parametric| Actor
    Router -->|retrieval_required| Condense[Condenser Node]
    
    Condense --> Retrieve[Retriever Node]
    Retrieve --> Evaluate{Structured Evaluator}
    
    Evaluate -->|Sufficient / Grounded| Actor
    Evaluate -->|Insufficient / Needs Revision| Rewrite[Rewriter Node]
    Rewrite --> Retrieve
    
    Actor --> StreamingResponse([Next.js Command Center])
```

### 1. The Traffic Cop (Intent Router)
A deterministic classifier powered by `llama-3.1-8b-instant` (0.0 temp) that flags query intent:
*   `direct_casual`: Greeting or helper capability queries. Bypasses database retrieval entirely.
*   `direct_parametric`: General coding syntax, logic proofs, or broad world facts. Bypasses database retrieval and utilizes LLM pre-trained weights.
*   `retrieval_required`: Specific, targeted queries requiring local indexed knowledge context.

### 2. The Strict RAG Loop (Research Path)
*   **The Senses (Hybrid Retriever):** Queries `pgvector` using ONNX-accelerated 384-dim dense embeddings (`fastembed`). Enforces `SIMILARITY_THRESHOLD = 0.35` to discard low-quality matches.
*   **The Critic (Structured Evaluator):** Evaluates retrieved context and returns a structured JSON payload:
    ```json
    {
      "relevant": true,
      "sufficient": false,
      "grounded": true,
      "confidence": 0.8,
      "retry_needed": false
    }
    ```
*   **The Strategist (Rewriter):** If context is relevant but insufficient, the rewriter reconstructs the search term using history. (Max 3 revision loops).
*   **The Actor (Dynamic Synthesis):** Generates responses strictly bound to the RAG context. Automatically formats responses into short, highly-readable paragraphs (max 2-3 sentences), structured lists, and airy spacing.

---

## ✨ Next.js Command Center (UI Features)

CodexEngine V4.0 features a custom-engineered Next.js dashboard configured for real-time observability:

*   **Pulsing Gradient Skeletons:** Animated loaders (`bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 animate-pulse`) that indicate routing/evaluation status.
*   **Stop Thinking Control:** Linked to an `AbortController` cancel request. Users can click inline or on the input bar stop buttons to terminate the pipeline instantly.
*   **Cognition Dashboard Panel:** Glassmorphic dashboard rendered above assistant replies, detailing structured evaluator outputs (relevance, sufficiency, groundedness, confidence, and intent).
*   **Superscript Footnote Citations:** Renders raw citations as compact footnote pills (e.g. `[p. 12]`, `[r. 5]`) with hover tooltips displaying full source names.
*   **Sliding Context Drawer:** Clicking any footnote slides out a context drawer showing the exact database chunk that grounded the claim.

---

## 🗂️ Project Structure

```text
CodexEngine/
├── codex-ui/                  # Next.js Command Center UI
│   ├── app/
│   │   ├── globals.css        # Tailwind styling & theme
│   │   ├── layout.tsx         # Brand metadata configuration
│   │   └── page.tsx           # SSE streaming, AbortController, and Context Drawer
│   └── package.json           # UI dependencies (lucide, react-markdown)
├── data/                      # PDF knowledge base staging
├── scripts/
│   └── ingestion.py           # V4 Prose-Aware (PyMuPDF) chunking & pgvector ingestion
├── src/
│   ├── state.py               # TypedDict AgentState schema
│   ├── repositories/
│   │   └── utils.py           # ONNX FastEmbed function
│   └── nodes/
│       ├── router.py          # Intent Router (few-shot prompting)
│       ├── retriever.py       # pgvector cosine similarity search (threshold: 0.35)
│       ├── evaluator.py       # Critic: JSON-structured context evaluator
│       ├── rewriter.py        # Strategist: Search query optimizer
│       ├── condenser.py       # Memory/history resolution
│       ├── actor.py           # Dynamic synthesis with short spacing rules
│       └── nodes.py           # Export hub
├── server.py                  # FastAPI server yielding SSE & history
├── requirements.txt           # Python backend dependencies
└── docker-compose.yml         # Containerized pgvector setup
```

---

## 🚀 Setup & Execution

### 1. Backend Setup
1.  **Clone & Configure env:**
    ```bash
    git clone <repository-url>
    cd CodexEngine
    ```
    Create a `.env` file:
    ```bash
    GROQ_API_KEY=gsk_your_groq_api_key_here
    DB_URL="postgresql+psycopg://anmol:6730@localhost:5432/codex_db"
    ```
2.  **Install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Spin up PostgreSQL (pgvector):**
    ```bash
    docker compose up -d
    ```
4.  **Ingest files:**
    Place raw PDFs in `data/raw/` and execute the modular ingestion:
    ```bash
    python scripts/ingestion.py
    ```
5.  **Start FastAPI Server:**
    ```bash
    python -m uvicorn server:app --reload --host 127.0.0.1 --port 8000
    ```

### 2. Frontend Setup
1.  **Install npm packages:**
    ```bash
    cd codex-ui
    npm install
    ```
2.  **Start development server:**
    ```bash
    npm run dev
    ```
    Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 💻 Verification & Testing

### Golden Queries Test
Verify custom citation link formats and evaluation score pipelines:
```bash
python tests/test_golden.py
```

### Rigorous Sweep Test
Verify agent self-correction loops across various academic, narratives, and technical files:
```bash
python tests/test_rigorous.py
```
Outputs are exported to `eval/v2_5_live_results.json` for validation.
