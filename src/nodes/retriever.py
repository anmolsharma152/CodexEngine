import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.state import AgentState
from src.utils import get_embedding_function

load_dotenv()
engine = create_engine(os.getenv("DB_URL"))
ef = get_embedding_function()

def retrieve_hybrid_context(state: AgentState) -> dict:
    # Use 'query' for first pass, or a potential 'rewritten_query' field if added
    current_search = state.query
    print(f"\n--- [RETRIEVING] Search Term: {current_search} ---")
    
    query_emb = ef([current_search])[0]
    
    # We use Cosine Similarity (<=>) for the vector match
    sql = text("""
        SELECT content 
        FROM prose_chunks 
        ORDER BY embedding <=> :emb 
        LIMIT 5;
    """)
    
    with engine.connect() as conn:
        results = conn.execute(sql, {"emb": str(query_emb.tolist())})
        context_chunks = [row[0] for row in results]

    return {
        "context": context_chunks,
        "next_step": "evaluate"
    }