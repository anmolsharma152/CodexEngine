import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DB_URL")
if not DB_URL:
    raise RuntimeError("DB_URL environment variable is not set")

engine = create_engine(DB_URL)


def ensure_schema():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS threads (
                id VARCHAR(255) PRIMARY KEY,
                user_id UUID NOT NULL,
                title VARCHAR(255) NOT NULL,
                timestamp BIGINT NOT NULL,
                pinned BOOLEAN DEFAULT FALSE
            );
        """))
        conn.execute(text("""
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'threads' AND column_name = 'user_id' AND data_type = 'integer'
                ) THEN
                    ALTER TABLE threads DROP CONSTRAINT IF EXISTS threads_user_id_fkey;
                    ALTER TABLE threads ALTER COLUMN user_id TYPE UUID USING '00000000-0000-0000-0000-000000000000'::uuid;
                END IF;
            END $$;
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prose_chunks (
                id BIGSERIAL PRIMARY KEY,
                content TEXT,
                metadata JSONB,
                embedding vector(384)
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prose_chunks_metadata ON prose_chunks USING GIN (metadata);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads (user_id);"))
        
        # Security: Enable Row Level Security (RLS) to block public API access
        conn.execute(text("ALTER TABLE threads ENABLE ROW LEVEL SECURITY;"))
        conn.execute(text("ALTER TABLE prose_chunks ENABLE ROW LEVEL SECURITY;"))
        
        conn.commit()
