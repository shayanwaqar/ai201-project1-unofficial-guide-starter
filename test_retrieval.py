#!/usr/bin/env python3
"""Run Milestone 4 retrieval smoke tests and save a markdown report."""

from __future__ import annotations

from pathlib import Path

from retrieve import DEFAULT_TOP_K, preview_text, retrieve


REPORT_PATH = Path("data/processed/retrieval_test_results.md")

TEST_QUERIES = [
    "What topics do students say are usually covered in CS3510?",
    "Why do students say CS4641 can be stressful or time-consuming?",
    "How do students distinguish CS3210 and CS3220?",
]


def format_result(result: dict) -> str:
    return "\n".join(
        [
            f"### Rank {result['rank']}",
            "",
            f"- Source: `{result['source']}`",
            f"- Chunk index: {result['chunk_index']}",
            f"- Distance: {result['distance']:.4f}",
            "",
            preview_text(result["text"], max_chars=900),
            "",
        ]
    )


def run_tests() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report_lines = ["# Retrieval Test Results", ""]

    for query in TEST_QUERIES:
        print(f"Query: {query}")
        results = retrieve(query, top_k=DEFAULT_TOP_K)

        report_lines.extend([f"## Query: {query}", ""])
        for result in results:
            print(
                f"  Rank {result['rank']}: {result['source']} "
                f"chunk {result['chunk_index']} distance={result['distance']:.4f}"
            )
            print(f"  Preview: {preview_text(result['text'], max_chars=300)}")
            print()
            report_lines.append(format_result(result))

        print("-" * 80)

    REPORT_PATH.write_text("\n".join(report_lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote retrieval report to: {REPORT_PATH}")


if __name__ == "__main__":
    run_tests()
