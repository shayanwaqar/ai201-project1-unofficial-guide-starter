# The Unofficial Guide

## Project Overview

The Unofficial Guide is a small RAG app for answering Georgia Tech CS course and student-experience questions from curated student discussion summaries. It is meant to answer practical questions about workload, difficulty, exams, projects, course combinations, systems courses, ML courses, and study advice.

The app uses local ingestion/chunking, local embeddings with ChromaDB retrieval, Groq generation, and a simple Gradio interface.

## Domain and Document Sources

The domain is Georgia Tech CS course/professor/student experience advice. This is useful because official course descriptions do not capture actual student experience, professor/semester variation, workload, exam style, or whether two courses are hard to combine.

The corpus has 10 manually curated `.txt` source briefs in `data/raw/`:

1. `01_cs3510_algorithms_topics_study_strategy.txt`
2. `02_gt_cs_hard_classes_cs3210_reputation.txt`
3. `03_cs2340_objects_design_difficulty_value.txt`
4. `04_cs_schedule_feasibility_1332_2110_2340_3600.txt`
5. `05_course_load_cs2110_cs1332_cs3750_cs2340.txt`
6. `06_cs1332_cs2110_finals_study_expectations.txt`
7. `07_cs4641_machine_learning_difficulty_workload.txt`
8. `08_cs2200_and_cs4641_combined_workload.txt`
9. `09_cs3210_credit_hours_workload_petition.txt`
10. `10_cs3210_vs_cs3220_comparison.txt`

## Chunking Strategy and Reasoning

`ingest.py` loads all raw `.txt` files, removes repeated whitespace and boilerplate corpus notes, and creates paragraph-aware chunks. The target chunk size is about 300-500 words with about 75 words of overlap when a document creates multiple chunks. Metadata preserves `source`, `chunk_index`, `word_count`, and a stable chunk `id`.

The final corpus currently produces 10 chunks from 10 short documents. This is expected because most source briefs are already around 300-380 words. Keeping each document as one chunk avoids tiny fragments that separate a course name from the actual student advice.

## Sample Chunks

Five labeled sample chunks are saved in `data/processed/chunk_samples.md`. The sample set includes:

- `01_cs3510_algorithms_topics_study_strategy__chunk_000`: CS3510 algorithms topics, proof/pseudocode focus, and study strategy.
- `03_cs2340_objects_design_difficulty_value__chunk_000`: CS2340 difficulty, tests, Android, project/design work, and value.
- `05_course_load_cs2110_cs1332_cs3750_cs2340__chunk_000`: Course-load advice for combining CS2110, CS1332, CS3750, and CS2340.
- `08_cs2200_and_cs4641_combined_workload__chunk_000`: Combined workload for CS2200 and CS4641.
- `10_cs3210_vs_cs3220_comparison__chunk_000`: CS3210 OS Design versus CS3220 Processor Design.

## Embedding Model and Production Tradeoffs

The embedding model is `sentence-transformers/all-MiniLM-L6-v2`. It is free, local, fast, and good enough for a small class-project corpus. ChromaDB stores the vectors persistently in `data/chroma/`, which is ignored by git.

For production, I would compare stronger embedding models on exact course-code matching, informal student language, latency, cost, context length, multilingual support, and domain-specific performance. This project shows that pure semantic similarity can miss exact identifiers like `CS3510`, so a production version should add course-code filtering or reranking.

## Retrieval Test Results

`test_retrieval.py` writes `data/processed/retrieval_test_results.md`.

Summary of three retrieval tests:

| Query                                                          | Result summary                                                                                              |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| What topics do students say are usually covered in CS3510?     | The CS3510 chunk was retrieved, but ranked second behind a broader course-load chunk.                       |
| Why do students say CS4641 can be stressful or time-consuming? | Retrieved the combined CS2200/CS4641 workload chunk first and the dedicated CS4641 difficulty chunk second. |
| How do students distinguish CS3210 and CS3220?                 | Correctly retrieved the CS3210-vs-CS3220 comparison chunk first.                                            |

## Grounded Generation

`query.py` calls `retrieve()` first, then sends only the retrieved chunks to Groq model `llama-3.3-70b-versatile`. The system prompt tells the model to use only the provided context, not general knowledge, and to say:

> I don't have enough information to answer that from the provided documents.

Source filenames are appended programmatically after generation, so source attribution does not depend only on the LLM remembering to cite.

## Example Responses

Question: `Why might taking CS2200 and CS4641 together be difficult?`

Example answer: Taking CS2200 and CS4641 together can be difficult because CS2200 requires significant reading and fast-paced systems material, while CS4641 projects can take a lot of time to run and understand.

Question: `How do students distinguish CS3210 and CS3220?`

Example answer: Students describe CS3220 as more processor-design and implementation-heavy, while CS3210 is a deeper operating systems course with C, kernel work, virtual memory, user environments, and time-consuming labs.

## Out-of-Scope Refusal Example

For a question like `What is the best dining hall at Georgia Tech?`, the system should respond that it does not have enough information from the provided documents. The corpus only covers selected CS course/student-experience discussions, not dining or campus-life topics.

## Query Interface Description

`app.py` provides a Gradio web interface with:

- a textbox for the user question
- an Ask button
- an answer output
- a sources output
- a retrieved chunks display for debugging/inspection

The CLI is also available through `query.py`.

## Sample Interaction Transcript

```text
User: What topics do students say are usually covered in CS3510?
System: For CS3510, students describe the core as algorithms theory: dynamic programming, divide and conquer, graph problems, number theory, and NP-completeness.
Sources:
- 05_course_load_cs2110_cs1332_cs3750_cs2340.txt
- 01_cs3510_algorithms_topics_study_strategy.txt
- ...
```

## Evaluation Report Summary

`evaluate.py` writes `data/processed/evaluation_report.md` using the five planning questions. The strongest results were the CS4641 workload, CS2200+CS4641 combination, and CS3210-vs-CS3220 comparison questions. The weakest results were CS3510 questions, where retrieval sometimes ranked broader course-planning documents above the specific CS3510 document or missed the CS3510 document.

## Honest Failure Case

The known failure case is CS3510 retrieval ranking. The query `What topics do students say are usually covered in CS3510?` can retrieve a broader course-load document before the specific CS3510 algorithms document. The query `Is CS3510 more coding-heavy or proof-heavy?` can miss the specific CS3510 chunk entirely and cause the generator to refuse.

This is caused by the retrieval stage, not the generator. The corpus is small, each document is one chunk, and broad course-planning language can look semantically similar to specific course questions. A future fix would add exact course-code matching or reranking before sending chunks to the LLM.

## Spec Reflection

One way `planning.md` helped was that it made the chunking and retrieval choices concrete before implementation. The scripts followed the planned structure: paragraph-aware chunking, `all-MiniLM-L6-v2`, ChromaDB, `top_k=5`, and source filename metadata.

One way implementation diverged is that the current documents are short enough that each source became one chunk. The planned overlap logic still exists for longer future documents, but the current corpus does not need overlapping chunks. Another practical divergence is that retrieval quality shows a need for course-code reranking, which was not implemented because Milestone 6 focuses on evaluation artifacts rather than changing core behavior.

## AI Usage

Instance 1:

- What I gave the AI: the Milestone 3 chunking plan from `planning.md` and the requirement to use only the Python standard library.
- What it produced: `ingest.py`, including cleaning, paragraph-aware chunking, JSONL output, and sample chunk markdown.
- What I changed or overrode: I kept the implementation simple and allowed one chunk per short source document instead of forcing artificial splits.

Instance 2:

- What I gave the AI: the Milestone 4 and 5 requirements for ChromaDB retrieval, Groq generation, and Gradio.
- What it produced: `build_index.py`, `retrieve.py`, `query.py`, and `app.py`.
- What I changed or overrode: I added local-first model loading for retrieval so repeated runs do not keep checking Hugging Face, and I kept generated Chroma files out of git.

## How to Run Locally

Create `.env` in the repo root:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the pipeline:

```bash
python3 ingest.py
python3 build_index.py
python3 evaluate.py
python3 app.py
```

CLI query example:

```bash
python3 query.py "What topics do students say are usually covered in CS3510?"
```
