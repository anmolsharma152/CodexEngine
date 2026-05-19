import json
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from chromadb.utils import embedding_functions
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Load Groq API key
load_dotenv()

# --- THE ZERO-BLOAT WRAPPER ---
# Uses the lightweight engine already on your system from ingestion.py
class ONNXEmbeddingWrapper:
    def __init__(self):
        self.ef = embedding_functions.DefaultEmbeddingFunction()
    
    def embed_documents(self, texts):
        return self.ef(texts)
    
    def embed_query(self, text):
        # Format for Chroma and return as a plain list for LangChain compatibility
        result = self.ef([text])
        return result[0].tolist() if hasattr(result[0], 'tolist') else result[0]

# Configuration
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "codex_v2_hierarchy"
QUERIES_PATH = "eval/golden_queries.json"
RESULTS_PATH = "eval/baseline_results.json"

def run_baseline():
    print("🚀 Starting Zero-Bloat V1 Baseline Science Test...")
    
    embeddings = ONNXEmbeddingWrapper()
    
    # Connect to your hierarchical database
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )
    
    # Simulate V1: Top 3 small child chunks (approx 1200 tokens total)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # Setup the LLM
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    
    prompt = ChatPromptTemplate.from_template("""
    Answer the question based ONLY on the following context.
    If the context does not contain the answer, say "I don't know."
    
    Context: {context}
    
    Question: {question}
    """)
    
    with open(QUERIES_PATH, 'r') as f:
        data = json.load(f)
        
    results = []
    
    for item in data['dataset']:
        print(f"Testing: {item['eval_focus']}")
        print(f"Q: {item['question']}")
        
        # Dumb retrieval (Child chunks only)
        docs = retriever.invoke(item['question'])
        context_text = "\n---\n".join([doc.page_content for doc in docs])
        
        # Generation
        chain = prompt | llm
        response = chain.invoke({"context": context_text, "question": item['question']})
        
        print(f"A: {response.content[:100]}...\n") 
        
        results.append({
            "query_id": item['query_id'],
            "question": item['question'],
            "eval_focus": item['eval_focus'],
            "retrieved_context": context_text,
            "baseline_answer": response.content
        })
        
    # Save the output for Ragas scoring later
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"✅ Success! Baseline results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    run_baseline()