import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import os
import re
from sqlalchemy import create_engine, text
from src.utils import get_embedding_function
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DB_URL"))
ef = get_embedding_function()


def clean_text(t):
    return t.replace("\x00", "").strip()


def ingest_narrative():
    # 1. Setup Table with source tracking
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

    # 2. Process Files
    raw_path = "data/raw"
    for filename in os.listdir(raw_path):
        if not filename.endswith(".pdf"):
            continue

        print(f"--- Ingesting Narrative: {filename} ---")
        loader = PyPDFLoader(os.path.join(raw_path, filename))

        # We join the whole book into one stream to avoid 'Page Break' fragmentation
        full_text = " ".join([clean_text(page.page_content) for page in loader.load()])

        # Split into 1500-char blocks with 300-char overlap
        # This is the "Prose-Aware" sweet spot
        chunks = []
        for i in range(0, len(full_text), 1200):  # 1200 step = 300 overlap
            chunks.append(full_text[i : i + 1500])

        with engine.connect() as conn:
            for chunk in chunks:
                if len(chunk) < 200:
                    continue
                emb = ef([chunk])[0]
                conn.execute(
                    text(
                        "INSERT INTO prose_chunks (content, embedding, source_file) VALUES (:c, :e, :s)"
                    ),
                    {"c": chunk, "e": emb.tolist(), "s": filename},
                )
            conn.commit()
    print("✅ Narrative Ingestion Complete.")


if __name__ == "__main__":
    ingest_narrative()

