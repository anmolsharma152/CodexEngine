-- Run this in Supabase SQL Editor to initialize the database schema

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS threads (
    id VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    timestamp BIGINT NOT NULL,
    pinned BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS prose_chunks (
    id BIGSERIAL PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding vector(384)
);

CREATE INDEX IF NOT EXISTS idx_prose_chunks_metadata ON prose_chunks USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads (user_id);

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
