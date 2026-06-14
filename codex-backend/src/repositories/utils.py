import os
import re
from functools import lru_cache

from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()


class FastEmbedWrapper:
    def __init__(self):
        self.model = TextEmbedding()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, x)) for x in self.model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return list(map(float, next(self.model.embed([text]))))


def get_embedding_function():
    return FastEmbedWrapper()


emb = get_embedding_function()


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
    global _reranker
    if _reranker is not None:
        return _reranker
    from fastembed.rerank import Reranker

    _reranker = Reranker(
        model_name="Xenova/ms-marco-MiniLM-L-6-v2",
        local_files_only=False,
    )
    return _reranker
