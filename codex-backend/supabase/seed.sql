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
