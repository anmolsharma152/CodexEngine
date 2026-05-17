import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.state import AgentState
from src.utils import get_embedding_function

load_dotenv()
engine = create_engine(os.getenv("DB_URL"))
ef = get_embedding_function()


def retrieve_hybrid_context(state: AgentState) -> dict:
    current_search = state.query
    print(f"\n--- [RETRIEVING] Search Term: {current_search} ---")

    query_emb = ef([current_search])[0]

    # NEW: Selecting metadata along with content
    sql = text("""
        SELECT content, metadata 
        FROM prose_chunks 
        ORDER BY embedding <=> :emb 
        LIMIT 5;
    """)

    with engine.connect() as conn:
        results = conn.execute(sql, {"emb": str(query_emb.tolist())})
        context_chunks = []
        for row in results:
            content = row[0]

            # Since 'metadata' is currently just a TEXT string (the filename),
            # we handle it directly as a string instead of a dictionary.
            source = row[1] if row[1] else "Unknown Document"

            # Format the chunk so the LLM sees the source attached to the text
            context_chunks.append(f"[Source: {source}] {content}")

    return {"query": current_search, "context": context_chunks, "next_step": "evaluate"}
