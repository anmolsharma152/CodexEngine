import os
from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()


class FastEmbedWrapper:
    """
    A lightweight wrapper to make FastEmbed compatible with
    LangChain's expected embedding interface.
    """

    def __init__(self):
        # This automatically uses 'all-MiniLM-L6-v2' (384-dim) by default!
        self.model = TextEmbedding()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, x)) for x in self.model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return list(map(float, next(self.model.embed([text]))))


def get_embedding_function():
    """
    Returns a high-performance, lightweight ONNX-backed embedding engine.
    Generates identical 384-dimensional dense vectors to match your schema.
    """
    return FastEmbedWrapper()
