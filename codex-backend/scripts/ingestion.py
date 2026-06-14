import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import os
import re
import csv
import json
import fitz
from sqlalchemy import create_engine, text
from src.repositories.utils import get_embedding_function
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from src.log_utils import logger

load_dotenv()
engine = create_engine(os.getenv("DB_URL"))
ef = get_embedding_function()


def clean_text(t):
    return t.replace("\x00", "").strip()


def ingest_file(file_path: str, thread_id: str = None, user_id: str = None):
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    logger.info(f"Ingesting Document: {filename} (Type: {ext})")

    if not os.path.exists(file_path):
        logger.error(f"File not found at {file_path}")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=200)
    chunks_data = []

    if ext == ".pdf":
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = clean_text(page.get_text())
                if text.strip():
                    page_chunks = text_splitter.split_text(text)
                    for chunk_text in page_chunks:
                        chunks_data.append({
                            "content": chunk_text,
                            "metadata": {"source": filename, "page": page_num + 1, "thread_id": thread_id, "user_id": user_id}
                        })
            doc.close()
        except Exception as e:
            logger.error(f"Failed to ingest PDF {filename}: {e}")
            return

    elif ext == ".csv":
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=1):
                    row_text = json.dumps(row, indent=2)
                    chunks_data.append({
                        "content": row_text,
                        "metadata": {"source": filename, "row": row_num, "thread_id": thread_id, "user_id": user_id}
                    })
        except Exception as e:
            logger.error(f"Failed to ingest CSV {filename}: {e}")
            return

    elif ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            full_text = clean_text(f.read())
        if full_text.strip():
            txt_chunks = text_splitter.split_text(full_text)
            for chunk_text in txt_chunks:
                chunks_data.append({
                    "content": chunk_text,
                    "metadata": {"source": filename, "thread_id": thread_id, "user_id": user_id}
                })
    else:
        logger.warning(f"Unsupported file type {filename}")
        return

    if not chunks_data:
        logger.warning(f"No valid chunks extracted from {filename}")
        return

    logger.info(f"Embedding and inserting {len(chunks_data)} chunks...")
    texts = [c["content"] for c in chunks_data]
    embeddings = ef.embed_documents(texts)

    with engine.connect() as conn:
        for chunk, emb in zip(chunks_data, embeddings):
            conn.execute(
                text("INSERT INTO prose_chunks (content, metadata, embedding) VALUES (:content, :metadata, :embedding)"),
                {"content": chunk["content"], "metadata": json.dumps(chunk["metadata"]), "embedding": str(emb)}
            )
        conn.commit()

    logger.info(f"Ingestion of {filename} Complete.")


if __name__ == "__main__":
    raw_path = "data/raw"
    if not os.path.exists(raw_path):
        logger.info(f"Creating directory: {raw_path}")
        os.makedirs(raw_path, exist_ok=True)

    for fn in sorted(os.listdir(raw_path)):
        fpath = os.path.join(raw_path, fn)
        if os.path.isfile(fpath):
            ingest_file(fpath)
    logger.info("All Document Ingestion Complete.")
