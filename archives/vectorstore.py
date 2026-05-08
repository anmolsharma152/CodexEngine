import chromadb
import uuid

class VectorStore:
    def __init__(self):
        # Keep persistent storage
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # UPGRADE: Add metadata to force Cosine Similarity for better thematic/fiction retrieval
        self.collection = self.client.get_or_create_collection(
            name="rag_documents",
            metadata={"hnsw:space": "cosine"} 
        )

    def add_documents(self, documents, metadatas):
        """
        Adds text chunks and their associated metadata (page number, filename).
        """
        if not documents:
            return
            
        ids = [str(uuid.uuid4()) for _ in documents]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def similarity_search(self, query, k=4, allowed_sources=None):
        """
        Returns top documents, filtered by specific source files if provided.
        """
        where_clause = None
        
        # Build the metadata filter based on UI selection
        if allowed_sources:
            if len(allowed_sources) == 1:
                where_clause = {"source": allowed_sources[0]}
            elif len(allowed_sources) > 1:
                where_clause = {"source": {"$in": allowed_sources}}

        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where_clause
        )
        
        # Return both the text chunks and the metadata (for citations)
        if results and results['documents'] and len(results['documents'][0]) > 0:
            return results['documents'][0], results['metadatas'][0]
        return [], []