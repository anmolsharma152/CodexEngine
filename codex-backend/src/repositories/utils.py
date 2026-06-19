import os
import re
import time

import google.generativeai as genai
from dotenv import load_dotenv

from src.log_utils import logger

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class GeminiEmbeddingWrapper:
    def __init__(self):
        self._model = "models/embedding-001"

    def _embed(self, texts: list[str]) -> list[list[float]]:
        try:
            result = genai.embed_content(model=self._model, content=texts, output_dimensionality=384)
            return result["embedding"]
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
        _embedding_model = APIEmbeddingWrapper()
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
