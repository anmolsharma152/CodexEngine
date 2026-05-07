import numpy as np
from rank_bm25 import BM25Okapi
from langchain_chroma import Chroma
from chromadb.utils import embedding_functions

# --- EMBEDDING WRAPPER ---
class ONNXEmbeddingWrapper:
    def __init__(self):
        self.ef = embedding_functions.DefaultEmbeddingFunction()
    def embed_documents(self, texts): return self.ef(texts)
    def embed_query(self, text):
        res = self.ef([text])
        return res[0].tolist() if hasattr(res[0], 'tolist') else res[0]

def retrieve_parent_context(state):
    print("\n--- [START] HYBRID AGENTIC RETRIEVAL ---")
    query = state["current_query"]
    embeddings = ONNXEmbeddingWrapper()
    
    vectorstore = Chroma(
        collection_name="codex_v2_hierarchy",
        persist_directory="chroma_db",
        embedding_function=embeddings
    )
    
    # 1. DENSE SEARCH (HNSW + Cosine)
    dense_results = vectorstore.similarity_search(query, k=5)
    
    # 2. SPARSE SEARCH (BM25)
    # Note: In a production V3, we would persist the BM25 index. 
    # For this transition, we'll build it from the vectorstore's current documents.
    all_docs = vectorstore.get()
    tokenized_corpus = [doc.split(" ") for doc in all_docs["documents"]]
    bm25 = BM25Okapi(tokenized_corpus)
    
    tokenized_query = query.split(" ")
    sparse_results = bm25.get_top_n(tokenized_query, all_docs["documents"], n=5)
    
    # 3. RECIPROCAL RANK FUSION (RRF)
    # We combine the results to find the most 'voted for' Parent blocks
    final_context_map = {}
    
    def apply_rrf(results, weight=1.0):
        for rank, doc in enumerate(results):
            # If doc is a string (from BM25) or Document (from Chroma)
            text = doc.page_content if hasattr(doc, 'page_content') else doc
            # Find metadata in all_docs for the corresponding text
            idx = all_docs["documents"].index(text)
            parent_text = all_docs["metadatas"][idx].get("parent_text", text)
            
            # RRF Formula: 1 / (k + rank)
            score = weight * (1.0 / (60 + rank))
            final_context_map[parent_text] = final_context_map.get(parent_text, 0) + score

    apply_rrf(dense_results, weight=1.0)
    apply_rrf(sparse_results, weight=1.0)
    
    # Sort by RRF score and take top 3
    # 1. Increase the pool: Sort by RRF score and take top 10 first
    sorted_context = sorted(final_context_map.items(), key=lambda x: x[1], reverse=True)[:10]
    # 2. Slice for the Actor: 
    # We take the top 5 blocks now. This gives the Evaluator more 'room' 
    # to find the answer without hitting the token limit too hard.
    context_blocks = [block[0] for block in sorted_context][:5]
    full_context = "\n---\n".join(context_blocks)
    print(f"Hybrid search fused {len(context_blocks)} Parent blocks into context.")
    return {"context": full_context}