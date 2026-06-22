import os
import re
import threading

import httpx
from dotenv import load_dotenv

from src.log_utils import logger

load_dotenv()

_GEMINI_BASE = "generativelanguage.googleapis.com"


class GeminiEmbeddingWrapper:
    def __init__(self):
        self._client = httpx.Client(timeout=30)
        self._model = "models/gemini-embedding-001"

    def _make_url(self):
        key = os.getenv("GOOGLE_API_KEY")
        return f"https://{_GEMINI_BASE}/v1beta/{self._model}:batchEmbedContents?key={key}"

    def _embed(self, texts: list[str]) -> list[list[float]]:
        import time
        try:
            url = self._make_url()
            headers = {"Content-Type": "application/json"}
            all_embeddings = []
            
            # Gemini batch limits are 100 requests per batch
            for i in range(0, len(texts), 100):
                if i > 0:
                    time.sleep(4)  # Base delay for 15 RPM limit
                    
                batch_texts = texts[i:i+100]
                
                # Retry logic for 429 Too Many Requests
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        resp = self._client.post(
                            url,
                            headers=headers,
                            json={
                                "requests": [{"model": self._model, "content": {"parts": [{"text": t}]}, "outputDimensionality": 384} for t in batch_texts]
                            },
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        all_embeddings.extend([e["values"] for e in data.get("embeddings", [])])
                        break  # Success, exit retry loop
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 429 and attempt < max_retries - 1:
                            logger.warning(f"Gemini 429 Too Many Requests. Retrying in {10 * (attempt + 1)} seconds...")
                            time.sleep(10 * (attempt + 1))
                        else:
                            raise
                            
            return all_embeddings
        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
            raise

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


class FastEmbedWrapper:
    def __init__(self):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [e.tolist() for e in self._model.passage_embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(self._model.query_embed([text])).tolist()


_embedding_model = None


def _low_memory() -> bool:
    if os.environ.get("RENDER") == "true":
        return True
    try:
        path = "/sys/fs/cgroup/memory.max"
        if os.path.exists(path):
            with open(path) as f:
                raw = f.read().strip()
                if raw != "max":
                    return int(raw) < 1.5 * 1024**3
    except Exception:
        pass
    try:
        path = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
        if os.path.exists(path):
            with open(path) as f:
                val = int(f.read().strip())
                if val > 0:
                    return val < 1.5 * 1024**3
    except Exception:
        pass
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return kb < 1_500_000
    except Exception:
        pass
    return False


def get_embedding_function():
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model
    if _low_memory():
        logger.info("Low-memory environment detected, using Gemini API for embeddings")
        _embedding_model = GeminiEmbeddingWrapper()
    else:
        try:
            _embedding_model = FastEmbedWrapper()
            logger.info("Using fastembed (local ONNX) for embeddings")
        except Exception as e:
            logger.warning(f"fastembed unavailable, falling back to Gemini API: {e}")
            _embedding_model = GeminiEmbeddingWrapper()
    return _embedding_model


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


_bm25_index = None
_bm25_corpus = []
_bm25_metadatas: list[dict] = []
_bm25_doc_ids: list[int] = []
_bm25_chunk_count = 0
_bm25_lock = threading.Lock()


def get_bm25_index(force_refresh=False):
    global _bm25_index, _bm25_corpus, _bm25_metadatas, _bm25_doc_ids, _bm25_chunk_count

    from rank_bm25 import BM25Okapi
    from sqlalchemy import text
    from src.db import engine

    with _bm25_lock:
        with engine.connect() as conn:
            current_count = conn.execute(text("SELECT COUNT(*) FROM prose_chunks")).scalar()

        if _bm25_index is not None and not force_refresh and current_count == _bm25_chunk_count:
            return _bm25_index, _bm25_corpus, _bm25_metadatas, _bm25_doc_ids

        with engine.connect() as conn:
            rows = conn.execute(text("SELECT content, metadata FROM prose_chunks")).fetchall()

        _bm25_corpus = []
        _bm25_metadatas = []
        for r in rows:
            if r[0]:
                _bm25_corpus.append(r[0])
                _bm25_metadatas.append(r[1] or {})
        tokenized_corpus = [tokenize(doc) for doc in _bm25_corpus]
        _bm25_index = BM25Okapi(tokenized_corpus)
        _bm25_doc_ids = list(range(len(_bm25_corpus)))
        _bm25_chunk_count = current_count
        return _bm25_index, _bm25_corpus, _bm25_metadatas, _bm25_doc_ids


_reranker = None


def get_reranker():
    global _reranker
    if _reranker is not None:
        return _reranker
    if _low_memory():
        logger.info("Low-memory environment detected, skipping local reranker")
        return None
    try:
        from fastembed.rerank import CrossEncoder
        _reranker = CrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")
        logger.info("Using CrossEncoder reranker (local ONNX)")
    except Exception as e:
        logger.warning(f"Reranker unavailable: {e}")
        _reranker = None
    return _reranker
