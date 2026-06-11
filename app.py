#!/usr/bin/env python3
"""Simple Gradio interface for The Unofficial Guide."""

from __future__ import annotations

import os
import socket

import gradio as gr

from query import ask
from retrieve import preview_text


def find_open_port(start: int = 7860, end: int = 8050) -> int:
    requested_port = os.getenv("GRADIO_SERVER_PORT")
    if requested_port:
        return int(requested_port)

    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"Could not find an open local port in range {start}-{end}.")


def format_retrieved_chunks(chunks: list[dict]) -> str:
    if not chunks:
        return "No chunks retrieved."

    lines = []
    for chunk in chunks:
        lines.extend(
            [
                f"## Rank {chunk['rank']}",
                f"- Source: `{chunk['source']}`",
                f"- Chunk index: {chunk['chunk_index']}",
                f"- Distance: {chunk['distance']:.4f}",
                "",
                preview_text(chunk["text"], max_chars=900),
                "",
            ]
        )
    return "\n".join(lines).strip()


def answer_question(question: str) -> tuple[str, str, str]:
    try:
        result = ask(question)
    except Exception as exc:
        message = str(exc)
        if "data/chroma" in message or "Chroma collection" in message:
            message = f"{message}\n\nRun `python3 build_index.py`, then try again."
        return f"Error: {message}", "", ""

    sources = "\n".join(result["sources"])
    retrieved_chunks = format_retrieved_chunks(result["retrieved_chunks"])
    return result["answer"], sources, retrieved_chunks


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown("# The Unofficial Guide")
    gr.Markdown("Ask about Georgia Tech CS courses using the indexed student discussion documents.")

    question = gr.Textbox(
        label="Question",
        placeholder="What topics do students say are usually covered in CS3510?",
        lines=3,
    )
    ask_button = gr.Button("Ask", variant="primary")

    answer = gr.Textbox(label="Answer", lines=10)
    sources = gr.Textbox(label="Sources", lines=5)
    retrieved_chunks = gr.Markdown(label="Retrieved chunks")

    ask_button.click(
        fn=answer_question,
        inputs=question,
        outputs=[answer, sources, retrieved_chunks],
    )
    question.submit(
        fn=answer_question,
        inputs=question,
        outputs=[answer, sources, retrieved_chunks],
    )


if __name__ == "__main__":
    port = find_open_port()
    print(f"Launching Gradio app at http://127.0.0.1:{port}")
    demo.launch(server_name="127.0.0.1", server_port=port)
