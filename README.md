# 🏛️ CodexEngine - Universal RAG Assistant

An enterprise-grade, blazing-fast Retrieval-Augmented Generation (RAG) application. This platform allows users to chat natively with complex PDF documents using advanced semantic search and dynamic, multi-provider LLM routing. 

## 🚀 Current Architecture (V1)

- **UI**: Streamlit with custom low-contrast dark mode.
- **LLM Orchestration**: LiteLLM (supporting Groq, OpenAI, Gemini).
- **Vector Database**: ChromaDB using **Cosine Similarity** for thematic retrieval.
- **Chunking Strategy**: Custom **Recursive Character Splitting** to maintain sentence and paragraph integrity.
- **Persistence**: Chat history is persisted via local JSON; document vectors are stored in `./chroma_db`.

## ✨ Features

- **Contextual Query Rewriting**: Follow-up questions are automatically contextualized based on conversation history.
- **Source Attributions**: Every answer includes [Source | Page] citations.
- **Multi-Document Support**: Ability to target specific documents or search the entire repository.
* **Multi-Provider LLM Routing:** Built on `LiteLLM`, allowing seamless switching between Groq, OpenAI, Anthropic, and Google Gemini via the UI.
* **Conversational Memory:** Streamlit-powered chat interface that retains conversation history for natural, multi-turn follow-up questions.
* **Offline Privacy-First Embeddings:** Utilizes `ChromaDB` and the local `all-MiniLM-L6-v2` model to embed documents directly on your CPU—ensuring your sensitive data is never sent to a cloud embedding API.
* **Smart UI Architecture:** Includes dynamic sidebar settings, API key masking, and dedicated context expanders to verify LLM grounding and prevent hallucinations.

## 🗂️ Project Structure
```
codex_engine/
├── src/
│   ├── app.py                 # Main Streamlit application and Chat UI
│   ├── components/
│   │   └── sidebar.py         # Provider selection and API key management
│   └── utils/
│       ├── vectorstore.py     # ChromaDB local vector database management
│       └── llm_service.py     # LiteLLM routing and prompt engineering
├── requirements.txt           # Environment dependencies
├── .env                       # (Ignored) Local API keys
└── README.md                  # Project documentation
```

## 📂 Targeted Data Types

Tested against:
1. Technical Manuals (DBeaver v26.1)
2. High-Fantasy Fiction (*The Final Empire*)
3. Historical Non-Fiction (*The Age of Alchemy*)
4. Subjective Manuals (*Legacy Over Lust*)

## 🛤️ Roadmap to V2 (Agentic)

- [ ] **Hybrid Retrieval**: Integrate BM25 (keyword) + Dense (Vector) via Reciprocal Rank Fusion (RRF).
- [ ] **LangGraph Orchestration**: Move to a stateful, multi-node workflow.
- [ ] **Actor-Critic Loop**: Implement an automated evaluator to prevent "lazy" summarization.

## 🚀 Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd codex_engine
   ```

2. **Set up the virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   Make sure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables (Optional):**
   Create a .env file in the root directory to auto-fill your keys in the UI:
   
   Example:
   GROQ_API_KEY=your_groq_key_here
   OPENAI_API_KEY=your_openai_key_here

## 💻 Usage

To run the application, execute the following command in your terminal:
```bash
streamlit run src/app.py
```

Once the application is running, you can:
1. Select Provider: Choose your preferred LLM provider in the left sidebar.
2. Upload Documents: Add one or more PDF files to the Knowledge Base.
3. Chat: Ask complex, multi-hop reasoning questions about your documents in the chat interface.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.