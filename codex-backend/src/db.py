import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DB_URL")
if not DB_URL:
    raise RuntimeError("DB_URL environment variable is not set")

# Sync engine for scripts (ingestion runs in threads)
engine = create_engine(DB_URL)

# Async engine for server/agent — convert psycopg:// → asyncpg://
_async_url = DB_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://")
_async_url = _async_url.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(_async_url)


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
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id BIGSERIAL PRIMARY KEY,
                thread_id VARCHAR(255) NOT NULL,
                user_id UUID NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT,
                created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_thread ON chat_messages (thread_id, user_id, created_at);"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workspace_artifacts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id VARCHAR(255) NOT NULL,
                path VARCHAR(1024) NOT NULL,
                content TEXT NOT NULL,
                artifact_type VARCHAR(50) DEFAULT 'document',
                created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT,
                updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT,
                UNIQUE(project_id, path)
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_project ON workspace_artifacts (project_id, path);"))
        conn.commit()
