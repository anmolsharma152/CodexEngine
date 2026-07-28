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

-- Security: Enable Row Level Security (RLS) to block public API access
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE prose_chunks ENABLE ROW LEVEL SECURITY;

-- LangGraph dynamically created tables
ALTER TABLE IF EXISTS checkpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS checkpoint_blobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS checkpoint_writes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS checkpoint_migrations ENABLE ROW LEVEL SECURITY;

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

-- Seed baseline sample document chunks for initial retrieval & BM25 index initialization
INSERT INTO prose_chunks (content, metadata)
SELECT 'Multi-Agent RAG architecture combines Router, Retriever, Evaluator, and Actor nodes in an iterative self-correction loop.', '{"source": "Agentic Retrieval-Augmented Generation_ A Survey on Agentic RAG.pdf", "page": 1}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM prose_chunks LIMIT 1);

INSERT INTO prose_chunks (content, metadata)
SELECT 'Kelsier planned to use the Eleventh Metal to defeat the Lord Ruler by revealing past lives and spiritual connections.', '{"source": "The Final Empire - Brandon Sanderson.pdf", "page": 42}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM prose_chunks WHERE content LIKE 'Kelsier%');

