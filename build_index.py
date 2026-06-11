#!/usr/bin/env python3
"""Milestone 4: embed processed chunks and store them in ChromaDB."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


CHUNKS_PATH = Path("data/processed/chunks.jsonl")
CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "unofficial_guide_chunks"
MODEL_NAME = "all-MiniLM-L6-v2"


def load_chunks(path: Path = CHUNKS_PATH) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run python3 ingest.py first.")

    chunks = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
    return chunks


def load_embedding_model() -> SentenceTransformer:
    try:
        return SentenceTransformer(MODEL_NAME, local_files_only=True)
    except Exception:
        print(f"Model not found locally; downloading: {MODEL_NAME}")
        return SentenceTransformer(MODEL_NAME)


def build_index() -> None:
    chunks = load_chunks()
    if not chunks:
        raise ValueError(f"No chunks found in {CHUNKS_PATH}. Run python3 ingest.py first.")

    texts = [chunk["text"] for chunk in chunks]
    ids = [chunk["id"] for chunk in chunks]
    metadatas = [
        {
            "source": chunk["source"],
            "chunk_index": int(chunk["chunk_index"]),
            "word_count": int(chunk["word_count"]),
        }
        for chunk in chunks
    ]

    print(f"Chunks loaded: {len(chunks)}")
    print(f"Loading embedding model: {MODEL_NAME}")
    model = load_embedding_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings.tolist(),
    )

    print(f"Chunks indexed: {collection.count()}")
    print(f"Chroma persist path: {CHROMA_DIR.resolve()}")


if __name__ == "__main__":
    build_index()
