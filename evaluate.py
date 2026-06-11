#!/usr/bin/env python3
"""Run Milestone 6 evaluation questions and save a markdown report."""

from __future__ import annotations

from pathlib import Path

from query import ask
from retrieve import preview_text


REPORT_PATH = Path("data/processed/evaluation_report.md")

EVALUATION_CASES = [
    {
        "question": "What topics do students say are usually covered in CS3510?",
        "expected": (
            "CS3510 topics: dynamic programming, divide and conquer, graph algorithms, "
            "number theory/graph theory, NP-completeness; varies by professor."
        ),
        "judgment": "partially accurate",
    },
    {
        "question": "Is CS3510 more coding-heavy or proof-heavy?",
        "expected": "CS3510 style: more proof-heavy and pseudocode/math-focused than programming-heavy.",
        "judgment": "inaccurate",
    },
    {
        "question": "Why do students say CS4641 can be stressful or time-consuming?",
        "expected": (
            "CS4641 stress: time-consuming ML assignments/projects, long papers, "
            "algorithms that take time to run, broad tests, statistics background helps."
        ),
        "judgment": "accurate",
    },
    {
        "question": "Why might taking CS2200 and CS4641 together be difficult?",
        "expected": (
            "CS2200 + CS4641: CS2200 has systems reading/fast pace, CS4641 has "
            "time-consuming ML projects/conceptual work."
        ),
        "judgment": "accurate",
    },
    {
        "question": "How do students distinguish CS3210 and CS3220?",
        "expected": (
            "CS3210 vs CS3220: CS3220 is processor design/Verilog/FPGA/pipelining; "
            "CS3210 is OS, C/kernel work, virtual memory, time-consuming labs."
        ),
        "judgment": "accurate",
    },
]


def format_chunks(chunks: list[dict]) -> list[str]:
    lines = []
    for chunk in chunks:
        lines.extend(
            [
                f"### Retrieved rank {chunk['rank']}",
                "",
                f"- Source: `{chunk['source']}`",
                f"- Chunk index: {chunk['chunk_index']}",
                f"- Distance: {chunk.get('distance', 'n/a'):.4f}",
                "",
                preview_text(chunk["text"], max_chars=900),
                "",
            ]
        )
    return lines


def run_evaluation() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Evaluation Report", ""]

    for index, case in enumerate(EVALUATION_CASES, start=1):
        question = case["question"]
        print(f"Evaluating {index}: {question}")
        result = ask(question)

        lines.extend(
            [
                f"## {index}. {question}",
                "",
                f"**Expected answer:** {case['expected']}",
                "",
                "**System answer:**",
                "",
                result["answer"],
                "",
                "**Sources:**",
                "",
            ]
        )

        for source in result["sources"]:
            lines.append(f"- `{source}`")

        lines.extend(
            [
                "",
                f"**Accuracy judgment:** {case['judgment']}",
                "",
                "**Retrieved chunks:**",
                "",
            ]
        )
        lines.extend(format_chunks(result["retrieved_chunks"]))

    lines.extend(
        [
            "## Failure Case: CS3510 Retrieval Ranking",
            "",
            (
                "The CS3510 topics query sometimes retrieves a broader course-load document "
                "before the specific CS3510 algorithms document. The specific CS3510 chunk is "
                "still retrieved, but it may appear below a schedule-planning chunk."
            ),
            "",
            (
                "This is a retrieval-ranking issue caused by semantically similar course-planning "
                "language and a small corpus where each document is one chunk. Because the chunks "
                "are full-document summaries, a document about multiple CS classes can look "
                "semantically close to a course-topic question even when it is less specific."
            ),
            "",
            (
                "A future fix would add lightweight course-code filtering or reranking so exact "
                "matches like CS3510 are promoted above broader CS schedule documents."
            ),
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote evaluation report to: {REPORT_PATH}")


if __name__ == "__main__":
    run_evaluation()
