# Georgia Tech CS Unofficial Guide Corpus

This folder contains 10 source-brief documents for the AI201 Week 1 RAG project. The domain is Georgia Tech CS course/professor/course-load advice from public Reddit student discussions.

Use the `txt/` files for easiest ingestion into your RAG pipeline. The `pdf/` files are included because the project permits PDFs and because the source documents can be referenced as individual artifacts.

Important: these are curated source briefs, not full scraped Reddit dumps. In your README, describe the collection process honestly as manual collection + light cleaning + source-brief creation, and list the original URLs from `sources_manifest.csv`.

Recommended chunking for this corpus: paragraph-aware or section-aware chunks around 250-450 words with 50-100 word overlap. Each source brief is already organized into metadata, summary, extracted notes, answerable questions, and a sample grounded answer.

Suggested evaluation questions:
1. What do students say CS3510 usually covers?
2. Why do students warn against taking CS1332, CS2110, CS2340, and CS3600 together?
3. What makes CS4641 stressful according to students?
4. How do students distinguish CS3210 from CS3220?
5. Is CS3210 considered high workload, and why?

Suggested out-of-scope/failure question:
- Which professor will teach CS3510 next semester?
The corpus does not contain current registration data, so a grounded system should refuse or say it lacks enough information.
