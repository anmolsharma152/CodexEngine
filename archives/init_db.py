import psycopg2
from sqlalchemy import create_engine, Column, Integer, Text, String
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

# Use the password you set in the docker run command
DB_URL = "postgresql://postgres:your_password_here@localhost:5432/postgres"

Base = declarative_base()

class ProseChunk(Base):
    __tablename__ = 'prose_chunks'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    # UPDATED: 384 dimensions for all-MiniLM-L6-v2
    embedding = Column(Vector(384)) 
    # Store 'parent_text' and other tags directly
    parent_id = Column(String) 
    metadata_json = Column(Text)

def init_db():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.close()
    conn.close()
    
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)
    print("✅ pgvector extension enabled. Table 'prose_chunks' ready with 384-dim support.")

if __name__ == "__main__":
    init_db()