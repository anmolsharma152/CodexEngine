import os
import re
import socket

import httpx
from dotenv import load_dotenv

from src.log_utils import logger

load_dotenv()

_GEMINI_BASE = "generativelanguage.googleapis.com"
_GEMINI_IPV4 = None


def _resolve_gemini_ipv4():
    global _GEMINI_IPV4
    if _GEMINI_IPV4 is None:
        _GEMINI_IPV4 = socket.getaddrinfo(_GEMINI_BASE, 443, socket.AF_INET)[0][4][0]
    return _GEMINI_IPV4


class GeminiEmbeddingWrapper:
    def __init__(self):
        self._client = httpx.Client(timeout=30)
        self._model = "models/gemini-embedding-001"

    def _make_url(self):
        ip = _resolve_gemini_ipv4()
        key = os.getenv("GOOGLE_API_KEY")
        return f"https://{ip}/v1beta/{self._model}:embedContent?key={key}"

    def _embed(self, texts: list[str]) -> list[list[float]]:
        try:
            resp = self._client.post(
                self._make_url(),
                headers={"Host": _GEMINI_BASE, "Content-Type": "application/json"},
                json={
                    "requests": [{"model": self._model, "content": {"parts": [{"text": t}]}, "outputDimensionality": 384} for t in texts]
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return [e["values"] for e in data.get("embeddings", [])]
        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
            raise

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


_embedding_model = None


def get_embedding_function():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = GeminiEmbeddingWrapper()
    return _embedding_model


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


_bm25_index = None
_bm25_corpus = []
_bm25_metadatas: list[dict] = []
_bm25_doc_ids: list[int] = []


def get_bm25_index():
    global _bm25_index, _bm25_corpus, _bm25_metadatas, _bm25_doc_ids
    if _bm25_index is not None:
        return _bm25_index, _bm25_corpus, _bm25_metadatas, _bm25_doc_ids

    from rank_bm25 import BM25Okapi
    from sqlalchemy import create_engine, text

    engine = create_engine(os.getenv("DB_URL"))
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
    return _bm25_index, _bm25_corpus, _bm25_metadatas, _bm25_doc_ids


_reranker = None


def get_reranker():
    return None
