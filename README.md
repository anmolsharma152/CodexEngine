# 🏛️ CodexEngine V2 - Agentic RAG Architecture

An enterprise-grade, self-correcting Retrieval-Augmented Generation (RAG) system. CodexEngine V2 abandons the standard, fragile "Retrieve-Generate" pipeline in favor of a stateful, cyclic **Agentic Workflow** built on LangGraph.

By introducing hierarchical Parent-Child indexing and an autonomous Evaluator node, the engine proactively detects missing context, rewrites its own search queries, and loops back to the database—eliminating the "Semantic Horizon" and preventing zero-shot hallucinations.

## 🚀 The V2 Architecture: The Agentic Self-Reflection Loop

Standard RAG systems operate as Directed Acyclic Graphs (DAGs)—static pipelines that fail silently when retrieval misses the mark. CodexEngine V2 implements an **Agentic Actor-Critic workflow** using LangGraph to introduce autonomous error correction.

1. **The Senses (Retriever Node):** Employs Hierarchical RAG. It searches for highly specific 400-character "Child" anchors, but extracts embedded 2,000-character "Parent" context blocks directly from metadata, delivering massive context windows with only a single database hop.
2. **The Critic (Evaluator Node):** A deterministic LLM (Llama-3.3-70b, Temp=0) acts as a strict grader. It evaluates the retrieved context against the user's intent *before* generation.
   * *Cyclic Conditionality:* If the context is insufficient, the Critic intercepts the flow, dynamically rewrites the query for higher precision, and forces a re-retrieval loop.
3. **The Actor (Generator Node):** Only executes when the Critic explicitly validates the context. This guarantees zero-shot hallucination prevention and produces highly technical, factual synthesis.

## ✨ Key Technical Features

* **Stateful Orchestration:** Powered by `LangGraph`, managing complex routing, loop iteration limits, and memory state tracking across the Agentic cycle.
* **Zero-Bloat ONNX Embeddings:** Uses a custom wrapper to natively utilize ChromaDB's built-in ONNX engine, bypassing heavy `sentence-transformers` and PyTorch dependencies to save ~5GB of environment space.
* **Deterministic Inference:** Built around Groq's blazing-fast `llama-3.3-70b-versatile` API at `temperature=0` to ensure greedy decoding, maximum fact-preservation, and mathematical consistency in evaluation.
* **Hierarchical (Parent-Child) Indexing:** Decouples the *search payload* from the *generation payload* to solve the "Fragmented Context" problem inherent in standard Recursive Character Splitting.

## 🗂️ Project Structure
```
CodexEngine/
├── data/
│   └── raw/                   # Target PDF documents
├── eval/
│   ├── golden_queries.json    # The 5-question baseline dataset
│   └── v2_results.json        # Agentic performance outputs
├── scripts/
│   ├── ingestion.py           # V2 Hierarchical indexing (Parent embedded in Child metadata)
│   └── eval_baseline.py       # V1 Dumb-RAG baseline testing
├── src/
│   ├── graph.py               # LangGraph compilation and conditional edge routing
│   ├── state.py               # TypedDict for tracking queries, context, and iterations
│   └── nodes/
│       ├── retriever.py       # ONNX-based semantic search & Parent extraction
│       ├── evaluator.py       # The Critic: Context grading and query rewriting
│       └── actor.py           # The Generator: Final factual synthesis
├── app.py                     # Main Streamlit UI entry point
├── test_agent.py              # CLI execution script for the Agentic Loop
├── requirements.txt           # Lean, zero-bloat dependencies
└── .env                       # API keys (e.g., GROQ_API_KEY)
```

## 📂 Targeted Evaluation Data

The engine's self-correction capabilities are tested against a highly diverse corpus of complex, multi-domain documents to ensure robust cross-domain generalization:

* **AI Research & System Architecture:** Agentic RAG surveys, adversarial attacks on Multimodal LLMs, and deep learning for source code generation.
* **Geopolitics & Macroeconomics:** Spatial analysis (*Prisoners of Geography*), economic history (*Open Veins of Latin America*), and Anthropic Nowcasting reports.
* **Theoretical Computer Science:** Algorithmic bounds for open addressing.
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
   ```
5. **Initialize the Vector Database:**
   Place your PDFs in ```data/raw/``` and run the hierarchical ingestion:
   ```bash
   python scripts/ingestion.py
   ```

## 💻 Usage

To test the Agentic Actor-Critic loop and watch the Evaluator rewrite queries in real-time in your terminal:
```bash
python test_agent.py
```

## 🛤️ Roadmap to V2.5: The Production-Grade Evolution

CodexEngine is transitioning from a modular agentic framework to a production-ready RAG platform. The following features are currently being integrated to ensure enterprise-level scalability, reliability, and observability:

### 🏗️ Infrastructure & Scalability
* **PostgreSQL + pgvector Migration:** Moving beyond local vector files to a robust, relational backend capable of handling multi-tenant knowledge bases and millions of embeddings.
* **Async FastAPI Backbone:** Refactoring the core engine into an asynchronous API service to support non-blocking agentic loops and concurrent user sessions.
* **Pydantic Data Validation:** Implementing strict schema enforcement across all graph nodes to ensure system stability and prevent LLM-driven state corruption.

### 🧠 Hybrid Intelligence
* **Autonomous Web Search Node:** Integrating live internet search capabilities (Brave/Serper) to supplement local PDF context when the Critic identifies information gaps.
* **Local Cross-Encoder Re-ranking:** Slashing latency and Groq token costs by scoring retrieved chunks locally before passing them to the high-parameter LLM.

### 🎨 Enterprise Experience & MLOps
* **Next.js Command Center:** A complete frontend redesign, moving away from Streamlit to a professional dashboard featuring a "Knowledge Base Manager" and a real-time "Agentic Thought Trace."
* **CI/CD Benchmarking:** Automated GitHub Actions that trigger the evaluation suite on every push, ensuring accuracy never regresses during rapid scaling.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for more details.
