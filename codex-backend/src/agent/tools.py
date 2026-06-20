"""
Migrated RAG nodes as @tool functions for the agent loop.

Each LangGraph node from src/nodes/ becomes a callable tool
that the LLM can invoke dynamically.
"""

import json
import asyncio
import os
from sqlalchemy import text
from duckduckgo_search import DDGS

from src.agent.tool_registry import tool
from src.llm import get_chat_model
from src.db import engine
from src.repositories.utils import get_embedding_function, get_bm25_index, get_reranker, tokenize
from src.log_utils import logger

# Shared LLM instances
_router_llm = get_chat_model(temperature=0.0, max_retries=3)
_evaluator_llm = get_chat_model(temperature=0, max_retries=3)
_rewriter_llm = get_chat_model(temperature=0.2, max_retries=3)

SIMILARITY_THRESHOLD = 0.35
VECTOR_TOP_K = 10
BM25_TOP_K = 10
FINAL_TOP_K = 5


@tool
async def analyze_intent(query: str) -> str:
    """Classify a user query as 'direct_casual', 'direct_parametric', or 'retrieval_required'."""
    logger.info("Analyzing User Intent")

    query_sample = query[:1500] + "\n[Truncated for Routing...]" if len(query) > 1500 else query

    prompt = f"""
    You are a highly efficient routing system for an AI assistant. Classify the user query into exactly ONE of the following routing decisions:

    1. 'direct_casual': Greetings, small talk, pleasantries, questions about assistant capabilities (e.g. "Can you help me?"), or questions purely about the user's/assistant's identity. These can be answered directly without search.
    2. 'direct_parametric': General coding/programming syntax queries, general mathematical/logical proofs, or broad world knowledge queries that the AI can answer confidently and completely using its internal pre-trained knowledge without needing local documents.
    3. 'retrieval_required': Specific factual queries about literature, custom documents, DBeaver truststore settings, quantum physics, AI papers, or any specific topic that requires retrieval of indexed context to be grounded and accurate.

    EXAMPLES:
    - User Query: "hi there" -> output: direct_casual
    - User Query: "Can you help me search through my documents?" -> output: direct_casual
    - User Query: "what is your name?" -> output: direct_casual
    - User Query: "how to write a binary search in python" -> output: direct_parametric
    - User Query: "Explain distance vs logical error rate in surface codes" -> output: retrieval_required
    - User Query: "What was Kelsier's plan?" -> output: retrieval_required

    User Query: "{query_sample}"

    Output ONLY the routing decision name in lowercase (direct_casual, direct_parametric, or retrieval_required). Do not add any punctuation, intro, or explanation.
    """

    response = await _router_llm.ainvoke(prompt)
    intent = response.content.strip().lower()

    if intent not in ["direct_casual", "direct_parametric", "retrieval_required"]:
        intent = "retrieval_required"

    logger.info(f"Intent Classified: {intent.upper()}")
    return intent


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


@tool
async def vector_search(query: str, thread_id: str = "", user_id: str = "") -> str:
    """Search documents using vector similarity and BM25 hybrid search. Returns formatted context with source citations."""
    logger.info(f"Hybrid search: {query[:80]}...")

    try:
        ef = await asyncio.to_thread(get_embedding_function)
        query_emb = await asyncio.to_thread(ef.embed_query, query)
        vector_docs = await asyncio.to_thread(_vector_search, query_emb, thread_id or None, user_id or "")
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
async def web_search(query: str) -> str:
    """Search the web for current information. Returns formatted results with titles and snippets."""
    try:
        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=3))

        results = await asyncio.to_thread(_search)
        docs = []
        for r in results:
            content = f"Title: {r.get('title', '')}\nSnippet: {r.get('body', '')}\nURL: {r.get('href', '')}"
            docs.append({"content": content, "metadata": {"source": "web", "title": r.get("title", "")}, "score": 0.5, "source": "web"})

        context = await asyncio.to_thread(_format_chunks, docs)
        logger.info(f"Web search returned {len(docs)} results")
        return context
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return ""


def _parse_json_response(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        nl = content.find("\n")
        if nl != -1:
            content = content[nl:]
        if content.endswith("```"):
            content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except Exception as e:
        logger.error(f"JSON parse error: {e}. Raw: {content}")
        return {
            "relevant": False,
            "sufficient": False,
            "grounded": False,
            "confidence": 0.0,
            "retry_needed": True,
        }


@tool
async def evaluate_retrieval(query: str, context: str, revision_count: int = 0) -> str:
    """Evaluate whether the retrieved context is sufficient to answer the query. Returns JSON with relevant, sufficient, grounded, confidence, and retry_needed fields."""
    if not context.strip():
        logger.info("Context is empty")
        evaluation = {
            "relevant": False,
            "sufficient": False,
            "grounded": False,
            "confidence": 0.0,
            "retry_needed": revision_count < 3,
        }
        return json.dumps(evaluation)

    query_sample = query[:1500] + "\n[Truncated for Evaluation...]" if len(query) > 1500 else query

    prompt = f"""
    Evaluate the retrieved context's ability to answer the search query.
    QUERY: {query_sample}
    CONTEXT: {context}

    Respond strictly in raw JSON format with the following fields:
    - "relevant": boolean (true if the context contains information directly related to the query)
    - "sufficient": boolean (true if the context contains enough details to fully answer the query without external knowledge)
    - "grounded": boolean (true if the context is factual and not contradictory to general knowledge)
    - "confidence": float between 0.0 and 1.0 (rating the overall quality of the source context)
    - "retry_needed": boolean (true if the context is irrelevant or insufficient AND we should rewrite and try retrieving again)

    Output ONLY the raw JSON block. Do not include any markdown styling, explanation, or other text.
    """

    response = await _evaluator_llm.ainvoke(prompt)
    evaluation = _parse_json_response(response.content)
    evaluation["retry_needed"] = evaluation.get("retry_needed", False) and revision_count < 3
    logger.info(f"Evaluation: {evaluation}")
    return json.dumps(evaluation)


@tool
async def rewrite_query(query: str, context: str = "") -> str:
    """Rewrite a search query to find better results when the previous search was insufficient."""
    context_samples = context[:500] if context else "No context found yet."

    prompt = f"""
    The previous search for "{query}" was insufficient.

    CONTEXT SAMPLES: {context_samples}

    TASK: Generate a single, highly-targeted search query to find the missing info.
    Return ONLY the new search string without quotes.
    """

    response = await _rewriter_llm.ainvoke(prompt)
    new_query = response.content.strip().replace('"', "")
    logger.info(f"Rewritten query: {new_query}")
    return new_query
