# 🏛️ CodexEngine V3.0 - High-Speed Agentic RAG

An enterprise-grade, stateful Retrieval-Augmented Generation (RAG) system. CodexEngine V3.0 evolves beyond basic query pipelines by introducing **Tri-Lane Intent Routing**, persistent multi-turn conversational memory, and a blazing-fast ONNX-backed vector infrastructure via PostgreSQL (`pgvector`).

## 🚀 The V3.0 Architecture: The Traffic Cop & The Agentic Loop

Standard RAG systems bleed tokens and latency by forcing every message through an expensive database retrieval loop. CodexEngine V3.0 uses a specialized **Intent Router** to classify user queries in milliseconds, splitting traffic into three distinct lanes:

1. **The Traffic Cop (Router Node):** A lightweight LLM (Llama 3.1 8B) instantly flags the query as `casual`, `explanatory`, or `research`.
2. **The Fast Paths (Casual & Explanatory):** Greetings, small talk, and general knowledge questions completely bypass the database. The 70B Actor responds instantly using chat history or its internal pre-trained knowledge.
3. **The Strict RAG Path (Research):** Fact-based queries trigger the Agentic Loop:
    * **The Senses (Hybrid Retriever):** Scans `pgvector` using ONNX-accelerated 384-dim embeddings (`fastembed`).
    * **The Critic (Evaluator):** A deterministic LLM grades retrieved context (0.0 - 1.0) *before* generation.
    * **The Strategist (Rewriter):** If the score is low, it dynamically rewrites the search query based on domain intent.
4. **The Shapeshifter (Actor Node):** The Llama 3.3 70B model dynamically alters its prompt rules based on the router lane, ensuring it is conversational for small talk but enforces strict anti-hallucination guardrails for research.

## ✨ Key Technical Features

* **Asynchronous FastAPI Backbone:** Fully decoupled backend architecture replacing legacy Streamlit UIs.
* **Stateful Memory Checkpointing:** Uses LangGraph's `AsyncPostgresSaver` to natively persist multi-turn conversations via simple `thread_id` injection.
* **Zero-Bloat Embeddings:** Ripped out the 2GB PyTorch footprint, executing local 384-dimensional dense vectors using Qdrant's lightweight `fastembed` C-compiled engine.
* **PostgreSQL + pgvector:** Enterprise-ready relational vector storage replacing fragile local file stores.

## 🗂️ Project Structure

```text
CodexEngine/
├── archives/                  # Legacy V1/V2 scripts and abandoned DBs
├── data/                      # Target PDF documents
├── scripts/
│   └── ingestion.py           # V3 Prose-Aware chunking and pgvector insertion
├── src/
│   ├── state.py               # Pydantic V2/TypedDict AgentState schema
│   ├── repositories/
│   │   └── utils.py           # ONNX FastEmbed function
│   └── nodes/
│       ├── router.py          # Llama 3.1 8B Intent Classifier
│       ├── retriever.py       # pgvector cosine similarity search
│       ├── evaluator.py       # The Critic: Context grading
│       ├── rewriter.py        # The Strategist: Intent-based query pivoting
│       ├── condenser.py       # Conversational memory resolution
│       ├── actor.py           # Dynamic role-aware synthesis
│       └── nodes.py           # Modular export hub
├── server.py                  # FastAPI Async Orchestrator & LangGraph setup
├── requirements.txt           # Lean dependencies (fastapi, fastembed, psycopg)
└── .env                       # Environment variables
```

## 📂 Targeted Evaluation Data

The engine's self-correction capabilities are rigorously benchmarked against a highly diverse corpus to ensure robust cross-domain generalization:

* **AI Research & System Architecture:** Agentic RAG surveys, adversarial attacks on Multimodal LLMs, and deep learning for source code generation.
* **Geopolitics & Macroeconomics:** Spatial analysis (*Prisoners of Geography*), economic history (*Open Veins of Latin America*), and Anthropic Nowcasting reports.
* **Quantum Physics:** Surface codes and logical error rate thresholds.
* **Sociopolitical Literature:** *India that is Bharat* axiological frameworks.
* **Technical Manuals:** DBeaver v26.1 database documentation and UI navigation.
* **High-Fantasy Fiction:** *The Final Empire* narrative logic and world-building.

## 🚀 Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd CodexEngine
   ````

2. **Set up the lean virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install zero-bloat dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a .env file in the root directory.

   ```bash
   GROQ_API_KEY=gsk_your_actual_key_here
   DB_URL="postgresql+psycopg://anmol:6730@localhost:5432/codex_db"
   ```

5. **Initialize the Vector Database:**
   Place your PDFs in ```data/raw/``` and run the ingestion script:

   ```bash
   python scripts/ingestion.py
   ```

6. **Start the API Server:**

   ```bash
   uvicorn server:app --reload
   ```

## 💻 Evals

To run the rigorous evaluation sweep and watch the Evaluator/Rewriter adapt to different domains in your terminal:

```bash
python -m scripts.test_rigorous
```

To test a specific, targeted query:

```bash
python scripts/test_golden.py
```

## 💻 Usage

Interact directly with the multi-turn agent via the unified chat endpoint. The graph will automatically maintain thread memory via the thread_id.

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Explain the architectural difference between a cross-encoder and bi-encoder.", 
       "thread_id": "session_1"
     }'
```

## 🛤️ Roadmap to V3.5: UI & Autonomous Expansion

With the V3 Backend optimized and secured, the next phase focuses on interface delivery and fail-safes.

### 🏗️ Infrastructure & Scalability

* **Async FastAPI Backbone:** Refactoring the core engine into an asynchronous API service (`server.py`) using Server-Sent Events (SSE) to stream the agentic "Thought Trace" (critic scores, rewrites) without blocking.
* **Next.js Command Center:** Building a decoupled Next.js/Vite frontend to consume the API, render markdown natively, and handle chat thread management.

### 🧠 Hybrid Intelligence

* **Autonomous Web Search Node:** Integrating live internet search capabilities (Tavily/DuckDuckGo) into the LangGraph routing. If the local Critic scores a retrieval at 0.0, the engine will automatically query the live web.
* **Local Cross-Encoder Re-ranking:** Slashing latency and Groq token costs by adding a local re-scoring layer (e.g., `ms-marco-MiniLM`). This will optimize the top 5 chunks retrieved by pgvector *before* they are passed to the high-parameter LLM.
* **Frontend Document Ingestion:** Building an /upload endpoint for drag-and-drop PDF indexing directly from the UI.

### ⚙️ Enterprise MLOps

* **CI/CD Benchmarking:** Implementing automated GitHub Actions (`eval.yml`) that trigger the `test_rigorous.py` evaluation suite on every push, ensuring Critic accuracy and retrieval precision never regress during rapid scaling.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for more details.
