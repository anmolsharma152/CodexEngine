import os
import json
from dotenv import load_dotenv
from langchain_chroma import Chroma
from chromadb.utils import embedding_functions
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

# Initialize Chroma
ef = embedding_functions.DefaultEmbeddingFunction()
vectorstore = Chroma(
    collection_name="codex_v2_hierarchy",
    persist_directory="chroma_db",
    embedding_function=ef
)

def migrate():
    print("--- Starting Migration: Chroma -> pgvector ---")
    all_docs = vectorstore.get(include=['documents', 'metadatas', 'embeddings'])
    
    session = Session()
    try:
        for i in range(len(all_docs["ids"])):
            # SCRUB: Remove null bytes from content and metadata
            content = all_docs["documents"][i].replace("\x00", "")
            embedding = all_docs["embeddings"][i].tolist() 
            metadata = all_docs["metadatas"][i]
            
            # Scrub the metadata keys/values too
            scrubbed_metadata = {k: (v.replace("\x00", "") if isinstance(v, str) else v) 
                                 for k, v in metadata.items()}
            
            stmt = text(
                "INSERT INTO prose_chunks (content, embedding, parent_id, metadata_json) "
                "VALUES (:content, :embedding, :parent_id, :metadata_json)"
            )
            
            session.execute(
                stmt,
                {
                    "content": content,
                    "embedding": embedding,
                    "parent_id": scrubbed_metadata.get("parent_text", "").replace("\x00", ""),
                    "metadata_json": json.dumps(scrubbed_metadata)
                }
            )
        
        session.commit()
        print(f"✅ Successfully migrated {len(all_docs['ids'])} chunks to pgvector.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    migrate()