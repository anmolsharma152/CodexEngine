# 🏛️ CodexEngine V2.5 - Production-Grade Agentic RAG

An enterprise-grade, self-correcting Retrieval-Augmented Generation (RAG) system. CodexEngine V2.5 completely replaces the fragile "Retrieve-Generate" pipeline with a stateful, cyclic **Agentic Workflow** built on LangGraph and powered by PostgreSQL (`pgvector`).

By introducing "Prose-Aware" chunking, dynamic intent detection, and a strict Critic node, the engine proactively detects missing context, rewrites its own search queries based on the domain (Academic vs. Narrative), and guarantees highly grounded synthesis.

## 🚀 The V2.5 Architecture: The Dynamic Agentic Loop

Standard RAG systems operate as Directed Acyclic Graphs (DAGs)—static pipelines that fail silently when retrieval misses the mark. CodexEngine V2.5 implements a **Typed Agentic workflow** using LangGraph to introduce autonomous error correction.

1. **The Senses (Retriever Node):** Employs `pgvector` for exact cosine-similarity search. It ingests documents using 1500-character "Prose-Aware" chunks (with 300-char overlap), providing massive, unbroken context windows that preserve narrative and academic flow.
2. **The Critic (Evaluator Node):** A deterministic LLM acts as a strict grader, scoring retrieved context from 0.0 to 1.0. It evaluates the context against the user's intent *before* generation.
3. **The Strategist (Rewriter Node):** If the Critic scores the context below 0.7, the flow routes here. The Rewriter detects the domain intent (e.g., Technical vs. Narrative) and dynamically shifts its search strategy—looking for "axiological frameworks" in academia, or "triggering events" in fiction.
4. **The Actor (Generator Node):** A role-aware synthesis engine. It shifts its persona (e.g., "Technical Analyst" vs "Narrative Analyst") to match the query, ensuring it never apologizes for a lack of "character motivation" when answering a quantum physics question.

## ✨ Key Technical Features

* **Stateful Orchestration:** Powered by `LangGraph`, managing complex routing and strictly typed via **Pydantic V2** (`AgentState`) to prevent LLM hallucination and "TPM Death Spirals."
* **PostgreSQL + pgvector:** Replaced local file-based vector stores (ChromaDB) with a robust, relational backend capable of handling enterprise scaling and exact mathematical vector matching.
* **Deterministic Inference:** Built around Groq's blazing-fast APIs. Evaluators use greedy decoding (`temperature=0`), while Actors are allowed slight creative nuance (`temperature=0.3`).
* **Universal Domain Adaptability:** The engine handles everything from SQL documentation to high-fantasy novels without manual configuration, automatically adjusting its "Logic Lean."

## 🗂️ Project Structure
```
CodexEngine/
├── archives/                  # Legacy V2 logic, abandoned Chroma DBs, and old tests
├── data/
│   └── raw/                   # Target PDF documents
├── eval/
│   ├── golden_queries.json    # The core cross-domain benchmark dataset
│   └── v2_5_live_results.json # Latest dynamic agentic performance outputs
├── scripts/
│   ├── ingestion.py           # V2.5 Prose-Aware chunking and pgvector insertion
│   ├── test_golden.py         # Single-query targeted testing
│   └── test_rigorous.py       # Full benchmark sweep across all domains
├── src/
│   ├── graph.py               # LangGraph compilation and conditional edge routing
│   ├── state.py               # Pydantic V2 AgentState schema
│   ├── utils.py               # Shared embedding functions
│   └── nodes/
│       ├── retriever.py       # pgvector cosine similarity search
│       ├── evaluator.py       # The Critic: Context grading (0.0 - 1.0)
│       ├── rewriter.py        # The Strategist: Intent-based query pivoting
│       └── actor.py           # The Generator: Role-aware factual synthesis
├── app.py                     # Main Frontend entry point (Streamlit/Chainlit)
├── requirements.txt           # Lean dependencies (pgvector, langgraph, pydantic)
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
   DB_URL=postgresql://user:password@localhost:5432/codex_db
   ```
5. **Initialize the Vector Database:**
   Place your PDFs in ```data/raw/``` and run the ingestion script:
   ```bash
   python scripts/ingestion.py
   ```

## 💻 Usage

To run the rigorous evaluation sweep and watch the Evaluator/Rewriter adapt to different domains in your terminal:
```bash
python -m scripts.test_rigorous
```

To test a specific, targeted query:
```bash
python scripts/test_golden.py
```

## 🛤️ Roadmap to V3.0: The Production SaaS Evolution

CodexEngine V2.5 has solidified the backend intelligence. The next phase focuses on user experience, API decoupling, and local optimization:

### 🏗️ Infrastructure & Scalability
* **Async FastAPI Backbone:** Refactoring the core engine into an asynchronous API service (`server.py`) using Server-Sent Events (SSE) to stream the agentic "Thought Trace" (critic scores, rewrites) without blocking.
* **Next.js Command Center:** A complete frontend redesign, moving away from Streamlit to a professional React-based dashboard featuring a "Knowledge Base Manager" and real-time execution logs.

### 🧠 Hybrid Intelligence
* **Autonomous Web Search Node:** Integrating live internet search capabilities (Tavily/DuckDuckGo) into the LangGraph routing. If the Critic identifies unresolvable information gaps within the local pgvector corpus, the graph will autonomously fallback to the web.
* **Local Cross-Encoder Re-ranking:** Slashing latency and Groq token costs by adding a local re-scoring layer (e.g., `ms-marco-MiniLM`). This will optimize the top 5 chunks retrieved by pgvector *before* they are passed to the high-parameter LLM.

### ⚙️ Enterprise MLOps
* **CI/CD Benchmarking:** Implementing automated GitHub Actions (`eval.yml`) that trigger the `test_rigorous.py` evaluation suite on every push, ensuring Critic accuracy and retrieval precision never regress during rapid scaling.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for more details.
