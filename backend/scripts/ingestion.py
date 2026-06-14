import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import os
import re
import csv
import fitz  # PyMuPDF
from sqlalchemy import create_engine, text
from src.repositories.utils import get_embedding_function
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import json

load_dotenv()
engine = create_engine(os.getenv("DB_URL"))
ef = get_embedding_function()


def clean_text(t):
    return t.replace("\x00", "").strip()


def ensure_table_exists():
    # Ensure table has the metadata column
    with engine.connect() as conn:
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS prose_chunks (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding VECTOR(384),
                metadata JSONB
            );
        """)
        )
        conn.commit()


def ingest_file(file_path: str, thread_id: str = None):
    ensure_table_exists()
    filename = os.path.basename(file_path)
    # If temporal/attached, strip the thread_id prefix from filename for cleaner citations
    citation_source = filename.split("_", 1)[1] if thread_id and filename.startswith(f"{thread_id}_") else filename
    ext = os.path.splitext(filename)[1].lower()
    print(f"--- Ingesting Document: {filename} (Type: {ext}) ---")

    if not os.path.exists(file_path):
        print(f"Error: file not found at {file_path}")
        return

    chunks_data = []  # List of tuples: (content_string, metadata_dict)

    if ext == ".pdf":
        try:
            doc = fitz.open(file_path)
            splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
            
            for page_index in range(len(doc)):
                page_num = page_index + 1
                page = doc[page_index]
                page_text = page.get_text()
                cleaned = clean_text(page_text)
                if not cleaned.strip():
                    continue

                # Split within the page
                splits = splitter.split_text(cleaned)
                for split in splits:
                    if len(split.strip()) < 100:  # Skip trivial chunks
                        continue
                    meta = {"source": citation_source, "page": page_num}
                    if thread_id:
                        meta["thread_id"] = thread_id
                    chunks_data.append((split, meta))
        except Exception as e:
            print(f"❌ Failed to ingest PDF {filename} using PyMuPDF: {e}")
            return

    elif ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        cleaned = clean_text(content)
        splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
        splits = splitter.split_text(cleaned)
        for split in splits:
            if len(split.strip()) < 100:
                continue
            meta = {"source": citation_source}
            if thread_id:
                meta["thread_id"] = thread_id
            chunks_data.append((split, meta))

    elif ext == ".csv":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                row_num = i + 1
                row_str = " | ".join([f"{k}: {v}" for k, v in row.items() if v is not None])
                if not row_str.strip():
                    continue
                meta = {"source": citation_source, "row": row_num}
                if thread_id:
                    meta["thread_id"] = thread_id
                chunks_data.append((row_str, meta))

    else:
        # Fallback to plain text reading
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            cleaned = clean_text(content)
            splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
            splits = splitter.split_text(cleaned)
            for split in splits:
                if len(split.strip()) < 100:
                    continue
                meta = {"source": citation_source}
                if thread_id:
                    meta["thread_id"] = thread_id
                chunks_data.append((split, meta))
        except Exception as e:
            print(f"❌ Failed to ingest unsupported file type {filename}: {e}")
            return

    # Insert all chunk data into the database
    if not chunks_data:
        print(f"⚠️ No valid chunks extracted from {filename}.")
        return

    print(f"Embedding and inserting {len(chunks_data)} chunks...")
    with engine.connect() as conn:
        for content, meta in chunks_data:
            emb = ef.embed_query(content)
            conn.execute(
                text(
                    "INSERT INTO prose_chunks (content, embedding, metadata) VALUES (:c, :e, :m)"
                ),
                {"c": content, "e": str(emb), "m": json.dumps(meta)},
            )
        conn.commit()

    print(f"✅ Ingestion of {filename} Complete.")


def ingest_narrative():
    # Process Files
    raw_path = "data/raw"
    if not os.path.exists(raw_path):
        print(f"Creating directory: {raw_path}")
        os.makedirs(raw_path, exist_ok=True)
        return

    for filename in os.listdir(raw_path):
        # Support PDF, TXT, MD, CSV in modular ingestion
        if not filename.endswith((".pdf", ".txt", ".md", ".csv")):
            continue
        file_path = os.path.join(raw_path, filename)
        ingest_file(file_path)

    print("✅ All Document Ingestion Complete.")


if __name__ == "__main__":
    ingest_narrative()
