#!/usr/bin/env python3
"""Milestone 4: semantic retrieval over the local ChromaDB index."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "unofficial_guide_chunks"
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 5


def load_embedding_model() -> SentenceTransformer:
    try:
        return SentenceTransformer(MODEL_NAME, local_files_only=True)
    except Exception as exc:
        raise RuntimeError(
            f"Embedding model '{MODEL_NAME}' is not cached locally. "
            "Run python3 build_index.py first with network access."
        ) from exc


def get_collection():
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(f"Missing {CHROMA_DIR}. Run python3 build_index.py first.")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        return client.get_collection(name=COLLECTION_NAME)
    except Exception as exc:
        raise RuntimeError(f"Missing Chroma collection '{COLLECTION_NAME}'. Run python3 build_index.py first.") from exc


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    """Return structured top-k semantic search results for Milestone 5."""
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    collection = get_collection()
    model = load_embedding_model()
    query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    rows = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances), start=1
    ):
        rows.append(
            {
                "rank": rank,
                "id": chunk_id,
                "source": metadata["source"],
                "chunk_index": metadata["chunk_index"],
                "word_count": metadata["word_count"],
                "distance": float(distance),
                "text": document,
            }
        )
    return rows


def preview_text(text: str, max_chars: int = 600) -> str:
    preview = " ".join(text.split())
    if len(preview) > max_chars:
        return preview[: max_chars - 3].rstrip() + "..."
    return preview


def print_results(query: str, results: list[dict[str, Any]]) -> None:
    print(f"Query: {query}")
    print(f"Results: {len(results)}")
    print()

    for result in results:
        print(f"Rank {result['rank']}")
        print(f"Source: {result['source']}")
        print(f"Chunk index: {result['chunk_index']}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Preview: {preview_text(result['text'])}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieve top matching chunks from ChromaDB.")
    parser.add_argument("query", help="Search query to embed and retrieve against the chunk index.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to retrieve.")
    args = parser.parse_args()

    print_results(args.query, retrieve(args.query, top_k=args.top_k))


if __name__ == "__main__":
    main()
