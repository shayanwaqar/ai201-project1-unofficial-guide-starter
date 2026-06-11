#!/usr/bin/env python3
"""Milestone 5: grounded Groq answers over retrieved course-advice chunks."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import APIConnectionError, APIError, AuthenticationError, Groq

from retrieve import DEFAULT_TOP_K, preview_text, retrieve


MODEL_NAME = "llama-3.3-70b-versatile"
ENV_PATH = Path(".env")
MISSING_INFO_MESSAGE = "I don't have enough information to answer that from the provided documents."


def load_api_key() -> str:
    if not ENV_PATH.exists():
        raise RuntimeError("Missing .env file. Create .env with GROQ_API_KEY=your_key before asking questions.")

    load_dotenv(ENV_PATH)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY. Add GROQ_API_KEY=your_key to .env.")
    return api_key


def format_context(chunks: list[dict[str, Any]]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(
            "\n".join(
                [
                    f"[Chunk {chunk['rank']}]",
                    f"Source: {chunk['source']}",
                    f"Chunk index: {chunk['chunk_index']}",
                    "Text:",
                    chunk["text"],
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


def build_messages(question: str, chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    context = format_context(chunks)
    system_prompt = (
        "You answer questions about Georgia Tech CS course and student experience advice. "
        "Use only the provided context. Do not use general knowledge. "
        f"If the context does not contain enough information, say exactly: {MISSING_INFO_MESSAGE}"
    )
    user_prompt = (
        "Context:\n"
        f"{context}\n\n"
        "Question:\n"
        f"{question}\n\n"
        "Answer from the context only. Be concise and practical."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def unique_sources(chunks: list[dict[str, Any]]) -> list[str]:
    sources = []
    seen = set()
    for chunk in chunks:
        source = chunk["source"]
        if source not in seen:
            seen.add(source)
            sources.append(source)
    return sources


def append_sources(answer: str, sources: list[str]) -> str:
    if not sources:
        return answer
    source_lines = "\n".join(f"- {source}" for source in sources)
    return f"{answer.strip()}\n\nSources:\n{source_lines}"


def ask(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    chunks = retrieve(question, top_k=top_k)
    sources = unique_sources(chunks)
    api_key = load_api_key()
    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=build_messages(question, chunks),
            temperature=0.1,
        )
    except AuthenticationError as exc:
        raise RuntimeError("Groq authentication failed. Check GROQ_API_KEY in .env.") from exc
    except APIConnectionError as exc:
        raise RuntimeError("Could not connect to Groq. Check your network connection and try again.") from exc
    except APIError as exc:
        raise RuntimeError(f"Groq API error: {exc}") from exc
    answer_text = response.choices[0].message.content or MISSING_INFO_MESSAGE
    answer_with_sources = append_sources(answer_text, sources)

    return {
        "answer": answer_with_sources,
        "sources": sources,
        "retrieved_chunks": chunks,
    }


def print_answer(result: dict[str, Any]) -> None:
    print(result["answer"])
    print()
    print("Retrieved chunks:")
    for chunk in result["retrieved_chunks"]:
        print(
            f"- Rank {chunk['rank']}: {chunk['source']} "
            f"chunk {chunk['chunk_index']} distance={chunk['distance']:.4f}"
        )
        print(f"  {preview_text(chunk['text'], max_chars=300)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a grounded question using Groq and retrieved chunks.")
    parser.add_argument("question", help="Question to answer from the indexed course-advice documents.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to retrieve.")
    args = parser.parse_args()

    try:
        print_answer(ask(args.question, top_k=args.top_k))
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    main()
