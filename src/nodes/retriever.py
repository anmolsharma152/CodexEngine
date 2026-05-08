import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.state import AgentState
from src.utils import get_embedding_function

load_dotenv()

engine = create_engine(os.getenv("DB_URL"))
ef = get_embedding_function()

def retrieve_hybrid_context(state: AgentState):
    # Use the mutable search_query
    current_search = state["search_query"]
    query_emb = ef([current_search])[0]
    
    sql = text("""
        SELECT content, metadata FROM prose_chunks 
        ORDER BY embedding <=> :emb LIMIT 5;
    """)

    with engine.connect() as conn:
        results = conn.execute(sql, {"emb": str(query_emb.tolist())})
        chunks = [f"[Source: {r[1].get('source')}] {r[0]}" for r in results]

    return {"context": "\n\n".join(chunks), "next_step": "evaluate"}