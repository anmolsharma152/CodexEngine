import os
import uuid
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

# Configuration Paths
DATA_PATH = "data/raw"
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "codex_v2_hierarchy"

def setup_chroma():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # This automatically defaults to the lightweight ONNX runtime
    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, 
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def build_v2_index():
    collection = setup_chroma()
    
    # The V2 Hierarchical Splitters
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

    pdf_files = [f for f in os.listdir(DATA_PATH) if f.endswith(".pdf")]
    
    for filename in pdf_files:
        print(f"--- Processing: {filename} ---")
        filepath = os.path.join(DATA_PATH, filename)
        
        try:
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            
            total_children = 0
            for doc in docs:
                # 1. Generate Parent Context Blocks (The "Big Picture" for the LLM)
                parent_chunks = parent_splitter.split_documents([doc])
                
                for p_chunk in parent_chunks:
                    parent_id = str(uuid.uuid4())
                    parent_text = p_chunk.page_content
                    
                    # 2. Generate Searchable Child Blocks (The "Needle" for ChromaDB)
                    child_chunks = child_splitter.split_text(parent_text)
                    
                    if not child_chunks:
                        continue
                        
                    ids = [str(uuid.uuid4()) for _ in child_chunks]
                    metadatas = [{
                        "parent_id": parent_id,
                        "parent_text": parent_text, 
                        "source": filename,
                        "page": doc.metadata.get("page", 0)
                    } for _ in child_chunks]
                    
                    # 3. Commit to ChromaDB
                    collection.add(
                        documents=child_chunks,
                        ids=ids,
                        metadatas=metadatas
                    )
                    total_children += len(child_chunks)
                    
            print(f"Success: Linked and indexed {total_children} child vectors for {filename}")
            
        except Exception as e:
            print(f"Failed to process {filename}: {str(e)}")

if __name__ == "__main__":
    print("Initializing CodexEngine V2 Hierarchical Ingestion...")
    build_v2_index()
    print("\nIngestion complete. The V2 Database is primed.")
