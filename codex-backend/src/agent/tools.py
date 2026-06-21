"""
Tools are external capabilities the LLM can't do on its own:
search user documents, search the web.

Everything else (intent classification, evaluating results, rewriting queries)
is just reasoning — the LLM does that directly.
"""

import asyncio
from sqlalchemy import text
from duckduckgo_search import DDGS

from src.agent.tool_registry import tool
from src.db import async_engine
from src.repositories.utils import get_embedding_function, get_bm25_index, get_reranker, tokenize
from src.log_utils import logger

SIMILARITY_THRESHOLD = 0.35
VECTOR_TOP_K = 10
BM25_TOP_K = 10
FINAL_TOP_K = 5


async def _vector_search(query_emb: list[float], thread_id: str | None, user_id_str: str) -> list[dict]:
    sql = text("""
        SELECT content, metadata, embedding <=> :emb as distance FROM prose_chunks
        WHERE (metadata->>'user_id' IS NULL AND metadata->>'thread_id' IS NULL)
           OR (metadata->>'user_id' = :user_id)
           OR (metadata->>'thread_id' = :thread_id)
        ORDER BY distance LIMIT :limit;
    """)
    async with async_engine.connect() as conn:
        results = await conn.execute(sql, {"emb": str(query_emb), "thread_id": thread_id, "user_id": user_id_str, "limit": VECTOR_TOP_K})
        docs = []
        for r in results:
            content = r[0]
            meta = r[1] or {}
            distance = r[2]
            similarity = 1.0 - distance
            if similarity >= SIMILARITY_THRESHOLD:
                docs.append({"content": content, "metadata": meta, "score": similarity, "source": "vector"})
        return docs


def _bm25_search(query_text: str) -> list[dict]:
    try:
        bm25, corpus, metadatas, doc_ids = get_bm25_index()
        tokenized_query = tokenize(query_text)
        scores = bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:BM25_TOP_K]
        docs = []
        for idx in top_indices:
            if scores[idx] > 0:
                docs.append({"content": corpus[idx], "metadata": dict(metadatas[idx]), "score": float(scores[idx]), "source": "bm25"})
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


def _format_chunks(docs: list[dict]) -> str:
    formatted = []
    for d in docs:
        meta = d.get("metadata", {})
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


@tool
async def search_documents(query: str, thread_id: str = "", user_id: str = "") -> str:
    """Search uploaded documents using vector similarity and keyword search. Returns relevant passages with source citations like [p. 5] or [doc]."""
    logger.info(f"Search documents: {query[:80]}...")

    try:
        ef = await asyncio.to_thread(get_embedding_function)
        query_emb = await asyncio.to_thread(ef.embed_query, query)
        vector_docs = await _vector_search(query_emb, thread_id or None, user_id or "")
    except Exception as e:
        logger.warning(f"Vector embedding failed, falling back to BM25-only: {e}")
        vector_docs = []

    bm25_docs = await asyncio.to_thread(_bm25_search, query)
    all_candidates = await asyncio.to_thread(_deduplicate, vector_docs + bm25_docs)

    if not all_candidates:
        logger.info("No local results found")
        return ""

    final_docs = await asyncio.to_thread(_rerank, query, all_candidates)
    context = await asyncio.to_thread(_format_chunks, final_docs)

    logger.info(f"Retrieved {len(vector_docs)} vector + {len(bm25_docs)} bm25 -> {len(final_docs)} final")
    return context


@tool
async def search_web(query: str) -> str:
    """Search the web for current information. Returns snippets with source URLs."""
    try:
        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=3))

        results = await asyncio.to_thread(_search)
        docs = []
        for r in results:
            content = f"Title: {r.get('title', '')}\nSnippet: {r.get('body', '')}\nURL: {r.get('href', '')}"
            docs.append({"content": content, "metadata": {"source": "web", "title": r.get("title", "")}, "score": 0.5, "source": "web"})

        context = _format_chunks(docs)
        logger.info(f"Web search returned {len(docs)} results")
        return context
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return ""


@tool
async def read_document(path: str, project_id: str = "", user_id: str = "") -> str:
    """Read a workspace artifact by path. Returns the full content."""
    logger.info(f"Read document: {path} project={project_id}")
    sql = text("SELECT content FROM workspace_artifacts WHERE path = :path AND project_id = :project_id;")
    async with async_engine.connect() as conn:
        res = await conn.execute(sql, {"path": path, "project_id": project_id})
        row = res.fetchone()
        if not row:
            return f"Error: no artifact found at '{path}' in this project."
        return row[0]
