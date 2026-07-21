-- Run this in Supabase SQL Editor to initialize the database schema

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS threads (
    id VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    timestamp BIGINT NOT NULL,
    pinned BOOLEAN DEFAULT FALSE
);

-- Fix legacy integer user_id column (pre-Supabase migration)
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'threads' AND column_name = 'user_id' AND data_type = 'integer'
    ) THEN
        ALTER TABLE threads DROP CONSTRAINT IF EXISTS threads_user_id_fkey;
        ALTER TABLE threads ALTER COLUMN user_id TYPE UUID USING '00000000-0000-0000-0000-000000000000'::uuid;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS prose_chunks (
    id BIGSERIAL PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding vector(384)
);

CREATE INDEX IF NOT EXISTS idx_prose_chunks_metadata ON prose_chunks USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads (user_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT,
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_thread ON chat_messages (thread_id, user_id, created_at);

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
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_project ON workspace_artifacts (project_id, path);

CREATE TABLE IF NOT EXISTS tool_invocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    tool_name VARCHAR(255) NOT NULL,
    arguments JSONB,
    result TEXT,
    error TEXT,
    duration_ms INTEGER,
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT
);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_thread ON tool_invocations (thread_id, created_at);

-- Security: Enable Row Level Security (RLS) to block public API access
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE prose_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_invocations ENABLE ROW LEVEL SECURITY;

-- Storage: create the 'documents' bucket (idempotent, skipped if not on Supabase)
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'storage' AND table_name = 'buckets') THEN
    INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
    VALUES ('documents', 'documents', false, 52428800, NULL)
    ON CONFLICT (id) DO NOTHING;
  END IF;
END $$;

-- Storage RLS policies for the 'documents' bucket (idempotent, skipped if not on Supabase)
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'storage' AND table_name = 'objects') THEN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can upload files' AND tablename = 'objects') THEN
      CREATE POLICY "Users can upload files" ON storage.objects
        FOR INSERT TO authenticated
        WITH CHECK (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can view their files' AND tablename = 'objects') THEN
      CREATE POLICY "Users can view their files" ON storage.objects
        FOR SELECT TO authenticated
        USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete their files' AND tablename = 'objects') THEN
      CREATE POLICY "Users can delete their files" ON storage.objects
        FOR DELETE TO authenticated
        USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);
    END IF;
  END IF;
END $$;
