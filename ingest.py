#!/usr/bin/env python3
"""Milestone 3 ingestion, cleaning, and chunking pipeline."""

from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
CHUNKS_PATH = PROCESSED_DIR / "chunks.jsonl"
SAMPLES_PATH = PROCESSED_DIR / "chunk_samples.md"

TARGET_MIN_WORDS = 300
TARGET_MAX_WORDS = 500
OVERLAP_WORDS = 75
MIN_CHUNK_WORDS = 120
SAMPLE_COUNT = 5


def word_count(text: str) -> int:
    return len(text.split())


def normalize_paragraph(paragraph: str) -> str:
    return re.sub(r"\s+", " ", paragraph).strip()


def clean_document(text: str) -> str:
    """Normalize whitespace and remove repeated empty lines plus corpus boilerplate."""
    paragraphs = []
    current_lines = []

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            if current_lines:
                paragraphs.append(normalize_paragraph(" ".join(current_lines)))
                current_lines = []
            continue

        # This note is the same across files and is not useful retrieval context.
        if line.startswith("Corpus note:"):
            continue

        current_lines.append(line)

    if current_lines:
        paragraphs.append(normalize_paragraph(" ".join(current_lines)))

    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def split_long_paragraph(paragraph: str, max_words: int = TARGET_MAX_WORDS) -> list[str]:
    """Fallback for unusually long paragraphs while keeping word boundaries intact."""
    words = paragraph.split()
    if len(words) <= max_words:
        return [paragraph]

    parts = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        parts.append(" ".join(words[start:end]))
        start = end
    return parts


def overlap_text(previous_chunk: str, overlap_words: int = OVERLAP_WORDS) -> str:
    words = previous_chunk.split()
    if len(words) <= overlap_words:
        return previous_chunk
    return " ".join(words[-overlap_words:])


def chunk_document(text: str) -> list[str]:
    """Create paragraph-aware chunks with word overlap for longer documents."""
    paragraphs = []
    for paragraph in text.split("\n\n"):
        paragraphs.extend(split_long_paragraph(paragraph.strip()))

    chunks = []
    current = []
    current_words = 0

    for paragraph in paragraphs:
        if not paragraph:
            continue

        paragraph_words = word_count(paragraph)
        would_exceed = current_words + paragraph_words > TARGET_MAX_WORDS

        if current and would_exceed and current_words >= TARGET_MIN_WORDS:
            chunk_text = "\n\n".join(current).strip()
            chunks.append(chunk_text)
            current = [overlap_text(chunk_text), paragraph]
            current_words = sum(word_count(part) for part in current)
        else:
            current.append(paragraph)
            current_words += paragraph_words

    if current:
        final_chunk = "\n\n".join(current).strip()
        if chunks and word_count(final_chunk) < MIN_CHUNK_WORDS:
            chunks[-1] = f"{chunks[-1]}\n\n{final_chunk}"
        elif word_count(final_chunk) > 0:
            chunks.append(final_chunk)

    return [chunk for chunk in chunks if word_count(chunk) >= MIN_CHUNK_WORDS or len(chunks) == 1]


def load_documents() -> list[tuple[Path, str]]:
    documents = []
    for path in sorted(RAW_DIR.glob("*.txt")):
        documents.append((path, path.read_text(encoding="utf-8")))
    return documents


def build_chunks(documents: list[tuple[Path, str]]) -> list[dict]:
    rows = []
    for path, raw_text in documents:
        cleaned = clean_document(raw_text)
        for chunk_index, chunk_text in enumerate(chunk_document(cleaned)):
            source = path.name
            rows.append(
                {
                    "id": f"{path.stem}__chunk_{chunk_index:03d}",
                    "source": source,
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "word_count": word_count(chunk_text),
                }
            )
    return rows


def write_jsonl(rows: list[dict]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with CHUNKS_PATH.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def select_samples(rows: list[dict], count: int = SAMPLE_COUNT) -> list[dict]:
    if len(rows) <= count:
        return rows

    step = (len(rows) - 1) / (count - 1)
    indexes = [round(i * step) for i in range(count)]
    return [rows[index] for index in indexes]


def write_samples(samples: list[dict]) -> None:
    lines = ["# Chunk Samples", ""]
    for sample in samples:
        lines.extend(
            [
                f"## {sample['id']}",
                "",
                f"- Source: `{sample['source']}`",
                f"- Chunk index: {sample['chunk_index']}",
                f"- Word count: {sample['word_count']}",
                "",
                sample["text"],
                "",
            ]
        )
    SAMPLES_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def print_summary(documents: list[tuple[Path, str]], rows: list[dict], samples: list[dict]) -> None:
    counts = [row["word_count"] for row in rows]
    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks created: {len(rows)}")
    if counts:
        print(f"Words per chunk: min={min(counts)}, max={max(counts)}, avg={mean(counts):.1f}")
    print(f"Wrote chunks to: {CHUNKS_PATH}")
    print(f"Wrote samples to: {SAMPLES_PATH}")
    print()
    print("Sample chunks:")
    for sample in samples:
        preview = sample["text"].replace("\n", " ")
        if len(preview) > 450:
            preview = preview[:447].rstrip() + "..."
        print(f"- {sample['id']} ({sample['source']}, {sample['word_count']} words)")
        print(f"  {preview}")


def main() -> None:
    documents = load_documents()
    rows = build_chunks(documents)
    samples = select_samples(rows)

    write_jsonl(rows)
    write_samples(samples)
    print_summary(documents, rows, samples)


if __name__ == "__main__":
    main()
