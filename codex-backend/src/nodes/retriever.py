import os
import asyncio
from functools import partial
from sqlalchemy import text
from src.state import AgentState
from src.repositories.utils import get_embedding_function, get_bm25_index, get_reranker, tokenize
from src.db import engine
from src.log_utils import logger

SIMILARITY_THRESHOLD = 0.35
VECTOR_TOP_K = 10
BM25_TOP_K = 10
FINAL_TOP_K = 5


def _vector_search(query_emb: list[float], thread_id: str | None, user_id_str: str) -> list[dict]:
    sql = text("""
        SELECT content, metadata, embedding <=> :emb as distance FROM prose_chunks
        WHERE (metadata->>'user_id' IS NULL AND metadata->>'thread_id' IS NULL)
           OR (metadata->>'user_id' = :user_id)
           OR (metadata->>'thread_id' = :thread_id)
        ORDER BY distance LIMIT :limit;
    """)
    with engine.connect() as conn:
        results = conn.execute(sql, {"emb": str(query_emb), "thread_id": thread_id, "user_id": user_id_str, "limit": VECTOR_TOP_K})
        docs = []
        for r in results:
            content = r[0]
            meta = r[1] or {}
            distance = r[2]
            similarity = 1.0 - distance
            if similarity >= SIMILARITY_THRESHOLD:
                docs.append({"content": content, "metadata": meta, "score": similarity, "source": "vector"})
        return docs


def _bm25_search(query_text: str, user_id_str: str) -> list[dict]:
    try:
        bm25, corpus, metadatas, doc_ids = get_bm25_index()
        tokenized_query = tokenize(query_text)
        scores = bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        docs = []
        for idx in top_indices:
            if scores[idx] > 0:
                meta = dict(metadatas[idx])
                doc_user = meta.get("user_id")
                if not doc_user or doc_user == user_id_str:
                    docs.append({"content": corpus[idx], "metadata": meta, "score": float(scores[idx]), "source": "bm25"})
                    if len(docs) >= BM25_TOP_K:
                        break
        return docs
    except Exception as e:
        logger.error(f"BM25 search failed: {e}")
        return []


def _rerank(query_text: str, candidates: list[dict]) -> list[dict]:
    reranker = get_reranker()
    if reranker is not None:
        try:
            pairs = [(query_text, d["content"]) for d in candidates]
            results = list(reranker.rerank(pairs))
            reranked = []
            for r in results:
                for d in candidates:
                    if d["content"] == r.text and d not in reranked:
                        d["rerank_score"] = r.score
                        reranked.append(d)
                        break
            reranked.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            return reranked[:FINAL_TOP_K]
        except Exception as e:
            logger.warning(f"Reranker failed, using score-based merge: {e}")
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:FINAL_TOP_K]


def _deduplicate(docs: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for d in docs:
        key = d["content"][:100]
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


async def _web_search(query_text: str) -> list[dict]:
    try:
        from duckduckgo_search import DDGS

        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(query_text, max_results=3))

        results = await asyncio.to_thread(_search)
        docs = []
        for r in results:
            content = f"Title: {r.get('title', '')}\nSnippet: {r.get('body', '')}\nURL: {r.get('href', '')}"
            docs.append({"content": content, "metadata": {"source": "web", "title": r.get("title", "")}, "score": 0.5, "source": "web"})
        logger.info(f"Web search returned {len(docs)} results")
        return docs
    except ImportError:
        logger.warning("duckduckgo_search not installed, skipping web search")
        return []
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


def _format_chunks(docs: list[dict]) -> str:
    formatted = []
    for d in docs:
        meta = d.get("metadata", {})
        source = meta.get("source", "Unknown Source")
        if d.get("source") == "web":
            ref = "[web]"
        elif "page" in meta:
            ref = f"[p. {meta['page']}]"
        elif "row" in meta:
            ref = f"[r. {meta['row']}]"
        else:
            ref = "[doc]"
        formatted.append(f"{ref}\n{d['content']}")
    return "\n\n".join(formatted)


async def retrieve_hybrid_context(state: AgentState, config=None):
    current_search = state["search_query"]

    thread_id = config.get("configurable", {}).get("thread_id", None) if config else None
    user_id = config.get("configurable", {}).get("user_id", None) if config else None
    user_id_str = str(user_id) if user_id is not None else ""

    try:
        ef = await asyncio.to_thread(get_embedding_function)
        query_emb = await asyncio.to_thread(ef.embed_query, current_search)
        vector_docs = await asyncio.to_thread(_vector_search, query_emb, thread_id, user_id_str)
    except Exception as e:
        logger.warning(f"Vector embedding failed, falling back to BM25-only: {e}")
        vector_docs = []

    bm25_docs = await asyncio.to_thread(_bm25_search, current_search, user_id_str)

    all_candidates = await asyncio.to_thread(_deduplicate, vector_docs + bm25_docs)

    if not all_candidates:
        logger.info("No local results — falling back to web search")
        web_docs = await _web_search(current_search)
        if web_docs:
            context = await asyncio.to_thread(_format_chunks, web_docs)
            return {"context": context, "next_step": "evaluate"}
        return {"context": "", "next_step": "evaluate"}

    final_docs = await asyncio.to_thread(_rerank, current_search, all_candidates)
    context = await asyncio.to_thread(_format_chunks, final_docs)

    logger.info(f"Retrieved {len(vector_docs)} vector + {len(bm25_docs)} bm25 → {len(final_docs)} final")
    return {"context": context, "next_step": "evaluate"}
