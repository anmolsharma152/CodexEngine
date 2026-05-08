from chromadb.utils import embedding_functions

# This ensures every node uses the same 384-dim model
def get_embedding_function():
    return embedding_functions.DefaultEmbeddingFunction()
