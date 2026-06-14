import os
import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.state import AgentState
from src.repositories.utils import get_embedding_function

load_dotenv()

engine = create_engine(os.getenv("DB_URL"))
ef = get_embedding_function()


SIMILARITY_THRESHOLD = 0.35


async def retrieve_hybrid_context(state: AgentState, config=None):
    # Use the mutable search_query
    current_search = state["search_query"]
    query_emb = ef.embed_query(current_search)

    thread_id = config.get("configurable", {}).get("thread_id", None) if config else None

    def _query_db():
        sql = text("""
            SELECT content, metadata, embedding <=> :emb as distance FROM prose_chunks 
            WHERE (metadata->>'thread_id' IS NULL OR metadata->>'thread_id' = :thread_id)
            ORDER BY distance LIMIT 5;
        """)
        with engine.connect() as conn:
            results = conn.execute(sql, {"emb": str(query_emb), "thread_id": thread_id})
            formatted_chunks = []
            for r in results:
                content = r[0]
                meta = r[1] or {}
                distance = r[2]
                similarity = 1.0 - distance
                
                # Retrieval thresholding: Discard noisy matches below 0.35 similarity
                if similarity < SIMILARITY_THRESHOLD:
                    continue
                
                source = meta.get("source", "Unknown Source")
                
                if "page" in meta:
                    ref = f"[Source: {source} | Page: {meta['page']}](citation://{source}?page={meta['page']})"
                elif "row" in meta:
                    ref = f"[Source: {source} | Row: {meta['row']}](citation://{source}?row={meta['row']})"
                else:
                    ref = f"[Source: {source}](citation://{source})"
                
                formatted_chunks.append(f"{ref}\n{content}")
            return formatted_chunks

    chunks = await asyncio.to_thread(_query_db)
    return {"context": "\n\n".join(chunks), "next_step": "evaluate"}
